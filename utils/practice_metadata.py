def add_document_metadata(chunks, doc_info):
    tagged_chunks = []
    
    for chunk in chunks:
        # YOUR CODE HERE
        # 1. Start with the existing chunk metadata
        # 2. Merge doc_info into it
        # 3. Build a new chunk dict with content + merged metadata
        # 4. Append to tagged_chunks
        existing_metadata = chunk["metadata"]
        merged_metadata = {**existing_metadata, **doc_info}
        tagged_chunks.append({"content":chunk["content"], "metadata": merged_metadata})
        pass
    
    return tagged_chunks


# Test it
from pipeline import final_chunks

doc_info = {
    "document_id": "TRV-POL-2005-V3",
    "policy_category": "Travel",
    "policy_owner": "GCT-RM",
    "effective_date": "2026-02-01"
}

tagged = add_document_metadata(final_chunks, doc_info)

for i, chunk in enumerate(tagged):
    print(f"--- Tagged Chunk {i+1} ---")
    print("Content:", chunk["content"])
    print("Metadata:", chunk["metadata"])
    print()