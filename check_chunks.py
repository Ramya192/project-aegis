import os
from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.environ["QDRANT_URL"],
    api_key=os.environ["QDRANT_API_KEY"]
)

col_name = "aegis_policies"

# Fetch all chunks for TRV-POL-1001-V4 (57 chunks — most likely to have long sections)
result, _ = client.scroll(
    collection_name=col_name,
    scroll_filter={
        "must": [{"key": "document_id", "match": {"value": "TRV-POL-1001-V4"}}]
    },
    limit=100,
    with_payload=True,
    with_vectors=False
)

# Sort by h2_header then chunk text start to get sequential order
chunks = sorted(result, key=lambda p: (
    p.payload.get("h2_header", ""),
    p.payload.get("chunk_text", "")[:30]
))

# Find pairs of chunks in the SAME h2 section with >40 words each
print("Checking overlap between consecutive chunks in SAME section (>40 words):\n")

found_pairs = 0
for i in range(len(chunks) - 1):
    curr = chunks[i]
    nxt  = chunks[i+1]

    # Only check same h2 section
    if curr.payload.get("h2_header") != nxt.payload.get("h2_header"):
        continue
    if not curr.payload.get("h2_header"):
        continue

    curr_text = curr.payload.get("chunk_text", "")
    next_text = nxt.payload.get("chunk_text", "")

    curr_words = curr_text.split()
    next_words = next_text.split()

    # Only check long enough chunks
    if len(curr_words) < 40 or len(next_words) < 40:
        continue

    found_pairs += 1

    # Check how many words from end of curr appear at start of next
    overlap_count = 0
    for window in range(5, 60):
        tail = " ".join(curr_words[-window:])
        if tail in next_text:
            overlap_count = window

    print(f"{'='*65}")
    print(f"Section : {curr.payload.get('h2_header')[:60]}")
    print(f"Chunk {i+1} ({len(curr_words)} words) → Chunk {i+2} ({len(next_words)} words)")
    print(f"Overlap detected : {overlap_count} words")
    print(f"\nEnd of chunk {i+1} (last 40 words):")
    print("  " + " ".join(curr_words[-40:]))
    print(f"\nStart of chunk {i+2} (first 40 words):")
    print("  " + " ".join(next_words[:40]))
    print()

if found_pairs == 0:
    print("No same-section chunk pairs with >40 words found in TRV-POL-1001-V4")
    print("Trying HR-POL-4001-V6 (38 chunks)...\n")

    result2, _ = client.scroll(
        collection_name=col_name,
        scroll_filter={
            "must": [{"key": "document_id", "match": {"value": "HR-POL-4001-V6"}}]
        },
        limit=100,
        with_payload=True,
        with_vectors=False
    )
    chunks2 = sorted(result2, key=lambda p: (
        p.payload.get("h2_header", ""),
        p.payload.get("chunk_text", "")[:30]
    ))

    for i in range(len(chunks2) - 1):
        curr = chunks2[i]
        nxt  = chunks2[i+1]
        if curr.payload.get("h2_header") != nxt.payload.get("h2_header"):
            continue
        if not curr.payload.get("h2_header"):
            continue