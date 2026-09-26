# chat.py
import os
import re
from collections import OrderedDict

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from qdrant_client import QdrantClient
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory

from retrieval.filters import detect_category, pre_filter_search, post_filter_by_date
from retrieval.retriever import generate_multi_queries, rrf_fuse
from retrieval.reranker import rerank
from retrieval.hyde import hyde_search
from utils.token_budget import enforce_token_budget

# In-memory chat histories, one per UI session. Bounded so a long-running public
# deployment can't grow without limit: the least recently used session is evicted.
MAX_SESSIONS = 200
MAX_HISTORY_MESSAGES = 10  # last 5 question/answer turns sent to the LLM
# Reranked chunks sent to the LLM. A question that spans two topics can rank its second topic's chunk
# just below 5, so keep a few more (the 3,000-token budget below still applies). The AEGIS_CONTEXT_CHUNKS
# environment variable exists for ablations.
CONTEXT_CHUNKS = int(os.getenv("AEGIS_CONTEXT_CHUNKS", "8"))
session_store: OrderedDict[str, InMemoryChatMessageHistory] = OrderedDict()

SYSTEM_PROMPT = """You are a corporate policy assistant.
Answer questions using ONLY the context below.
If the context does not contain the answer, say that you could not find it in the policy documents.
Be clear and helpful.
When the answer depends on a date, deadline or condition stated in the policy (for example "as of November 15th"), state it.

After your answer, add a final line in exactly this form, listing the [Source n] numbers your answer actually relies on:
SOURCES: 1, 3
Write "SOURCES: none" if the context did not contain the answer.

Context:
{context}"""

# Matches the trailing "SOURCES: 1, 3" line the model is asked to append
SOURCES_LINE = re.compile(r"\n*\s*SOURCES:\s*([^\n]*)\s*$", re.IGNORECASE)


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id in session_store:
        session_store.move_to_end(session_id)
    else:
        session_store[session_id] = InMemoryChatMessageHistory()
        while len(session_store) > MAX_SESSIONS:
            session_store.popitem(last=False)
    return session_store[session_id]


def clear_session(session_id: str) -> None:
    session_store.pop(session_id, None)


def build_context(chunks: list) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        source = chunk["metadata"].get("document_id", "Unknown")
        category = chunk["metadata"].get("policy_category", "")
        parts.append(f"[Source {i} - {source} ({category})]:\n{chunk['text']}")
    return "\n\n".join(parts)


def split_answer(raw: str, num_sources: int) -> tuple[str, set[int]]:
    """Separate the answer text from its trailing "SOURCES: ..." line.

    Returns the cleaned answer and the 0-based indexes of the sources the model cited.
    A missing or unparseable line yields an empty set, and the UI then falls back to score order.
    """
    match = SOURCES_LINE.search(raw)
    if not match:
        return raw.strip(), set()
    used = {int(n) - 1 for n in re.findall(r"\d+", match.group(1)) if 1 <= int(n) <= num_sources}
    return raw[:match.start()].strip(), used


def ask(query: str, session_id: str, qdrant: QdrantClient, openai_client: OpenAI, llm) -> dict:

    # Step 1: detect category (used as a pre-filter by every search below)
    category = detect_category(query, llm)

    # Step 2: generate multiple queries
    queries = generate_multi_queries(query, llm)

    # Step 3: search with pre-filter for each query variant
    ranked_lists = [
        pre_filter_search(q, qdrant, openai_client, category, top_k=13)
        for q in queries
    ]

    # Step 3b: HyDE search
    ranked_lists.append(
        hyde_search(query, qdrant, openai_client, llm, top_k=13, category=category)
    )

    # Step 4: RRF fusion → top 25
    fused_chunks = rrf_fuse(ranked_lists, limit=25)

    # Step 5: post filter by date
    filtered_chunks = post_filter_by_date(fused_chunks)

    # Step 6: rerank → top CONTEXT_CHUNKS
    final_chunks = rerank(query, filtered_chunks, top_k=CONTEXT_CHUNKS)

    # Step 7: enforce token budget
    final_chunks, token_info = enforce_token_budget(final_chunks, budget=3000)
    context = build_context(final_chunks)

    # Step 8: build prompt with chat history
    history = get_session_history(session_id)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{query}")
    ])

    # Step 9: get answer from LLM
    response = (prompt | llm).invoke({
        "context": context,
        "history": history.messages[-MAX_HISTORY_MESSAGES:],
        "query": query
    })

    answer, used = split_answer(str(response.content), len(final_chunks))

    # Step 10: save to history (without the SOURCES line)
    history.add_user_message(query)
    history.add_ai_message(answer)

    # Step 11: build sources list (rerank_score is already in [0, 1] for both rerankers).
    # "used" marks the passages the model cited; the score is only a retrieval-rank signal
    # (Cohere scores table rows and multi-topic answers low even when the answer depends on them).
    sources = [
        {
            "document_id": chunk["metadata"].get("document_id", "Unknown"),
            "score": round(float(chunk.get("rerank_score", 0)), 4),
            "text": chunk["text"],
            # the preamble chunk (Document ID, effective date) sits under the h1 only
            "section": chunk["metadata"].get("h2_header") or "Document header",
            "policy_category": chunk["metadata"].get("policy_category", ""),
            "effective_date": chunk["metadata"].get("effective_date", ""),
            "used": i in used,
        }
        for i, chunk in enumerate(final_chunks)
    ]

    return {
        "answer": answer,
        "sources": sources,
        "category_detected": " + ".join(category) if category else None,
        "token_info": token_info,
    }


if __name__ == "__main__":
    from service import run_query

    result = run_query("What is the maternity leave policy?", session_id="test_user_1")

    print(f"Category detected: {result['category_detected']}")
    print(f"\nAnswer:\n{result['answer']}")
    print("\nSources used:")
    for s in result["sources"]:
        print(f"  - {s['document_id']} | {s['section']}")
