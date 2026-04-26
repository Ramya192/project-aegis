from langchain_text_splitters import MarkdownHeaderTextSplitter
from table_splitter import split_large_table

markdown_text = """
# Corporate Travel Policy

## International Per Diems
Employees are entitled to a daily allowance based on destination.

| Destination | Daily Allowance |
|-------------|-----------------|
| USA         | $80             |
| Europe      | $70             |
| Asia        | $60             |
| Australia   | $90             |

## Ground Transportation
Taxis and rideshares are reimbursable up to $50 per trip.
"""

headers_to_split_on = [
    ("#", "h1_header"),
    ("##", "h2_header"),
    ("###", "h3_header"),
]

splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
chunks = splitter.split_text(markdown_text)

final_chunks = []

for chunk in chunks:
    content = chunk.page_content
    metadata = chunk.metadata

    # Check if this chunk contains a table
    if "|" in content:
        
        # Extract just the table portion from the content
        lines = content.split("\n")
        table_lines = [line for line in lines if line.strip().startswith("|")]
        table_text = "\n".join(table_lines)
        
        # Check if table has more than 3 data rows (header + separator + 3 rows = 5 lines)
        if len(table_lines) > 5:
            # YOUR CODE HERE
            # 1. Call split_large_table on table_text
            # 2. For each table chunk, append to final_chunks
            #    with the same metadata as the parent chunk
            table_chunks = split_large_table(table_text)
            for table_chunk in table_chunks:
                final_chunks.append({"content": table_chunk, "metadata": metadata})
            pass
        else:
            final_chunks.append({"content": content, "metadata": metadata})
    else:
        final_chunks.append({"content": content, "metadata": metadata})

# Print results
for i, chunk in enumerate(final_chunks):
    print(f"--- Final Chunk {i+1} ---")
    print("Content:", chunk["content"])
    print("Metadata:", chunk["metadata"])
    print()