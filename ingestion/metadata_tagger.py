import json
import re
from langchain_openai import ChatOpenAI

def extract_metadata(chunk_text: str, llm) -> dict:

    prompt = f"""
        You are a corporate policy document parser.
        Extract the following metadata from the text below.
        Return ONLY valid JSON, no explanation, no markdown.

        Fields to extract:
            - document_id: policy code if visible (e.g. TRV-POL-2005-V3), else null
            - policy_category: one of [Travel, HR, Finance, IT, Legal, Compliance, Other]
            - policy_owner: department name if mentioned, else null
            - effective_date: date in YYYY-MM-DD format if mentioned, else null

        Text:
        \"\"\"
        {chunk_text[:800]}
        \"\"\"

        JSON:
    """

    response = llm.invoke(prompt).content.strip()

    # Strip markdown code fences if the model wraps its output
    response = re.sub(r"```json|```", "", response).strip()

    try:
    # attempt something risky
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
    # if it fails, do this instead
        return {
        "document_id": None,
        "policy_category": "Other",
        "policy_owner": None,
        "effective_date": None
    }

def tag_chunks_with_metadata(chunks: list, llm) -> list:
    tagged = []
    
    for chunk in chunks:
        # Step 1: call extract_metadata on chunk["content"]
        llm_meta = extract_metadata(chunk["content"], llm)

        # Step 2: merge existing header metadata with LLM metadata
        full_metadata = {
            **chunk["metadata"],   # h1, h2, h3 from header splitter
            **llm_meta             # document_id, policy_category etc from LLM
        }

        # Step 3: append to tagged list
        tagged.append({
            "content": chunk["content"],
            "metadata": full_metadata
        })
    
    return tagged