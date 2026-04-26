import os
import glob
from openai import OpenAI
from pydantic import SecretStr
from qdrant_client import QdrantClient
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

from ingestion.chunker import chunk_markdown_document
from ingestion.metadata_tagger import extract_metadata
from ingestion.embedder import setup_qdrant_collection, upsert_chunks_batch, create_payload_indexes


def load_markdown_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def main():
    # --- Clients ---
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    qdrant_client = QdrantClient(
        url=os.environ["QDRANT_URL"],
        api_key=os.environ["QDRANT_API_KEY"],
        timeout=60
    )
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=SecretStr(os.environ["OPENAI_API_KEY"])
    )

    # --- Step 1: Chunk + Tag (per file) ---
    print("Step 1: Chunking and tagging...")
    all_tagged_chunks = []

    for md_file in glob.glob("data/**/*.md", recursive=True):
        print(f"  Loading: {md_file}")
        markdown_text = load_markdown_file(md_file)
        file_chunks = chunk_markdown_document(markdown_text)

        # LLM reads FIRST chunk only → extracts file-level metadata
        file_metadata = extract_metadata(file_chunks[0]["content"], llm)
        print(f"    → {len(file_chunks)} chunks | category: {file_metadata.get('policy_category')}")

        # Copy file_metadata to ALL chunks from this file
        for chunk in file_chunks:
            full_metadata = {
                **chunk["metadata"],
                **file_metadata
            }
            all_tagged_chunks.append({
                "content": chunk["content"],
                "metadata": full_metadata
            })

    print(f"\n  → {len(all_tagged_chunks)} total tagged chunks")

    # --- Step 2: Embed + Upsert ---
    print("\nStep 2: Embedding and upserting...")
    setup_qdrant_collection(qdrant_client)
    create_payload_indexes(qdrant_client)   
    upsert_chunks_batch(all_tagged_chunks, openai_client, qdrant_client)

    print("\n✅ Ingestion complete!")


if __name__ == "__main__":
    main()