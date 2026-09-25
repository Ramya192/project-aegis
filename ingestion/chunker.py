# chunker.py

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ingestion.table_splitter import split_large_table

def chunk_markdown_document(markdown_text: str, chunk_size: int = 500, overlap_pct: float = 0.12):

    # --- Header splitting ---
    headers_to_split_on = [
        ("#", "h1_header"),
        ("##", "h2_header"),
        ("###", "h3_header"),
    ]
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    header_chunks = header_splitter.split_text(markdown_text)

    # --- Overlap splitter setup ---
    overlap = int(chunk_size * overlap_pct)  # 12% of chunk_size
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    # --- Loop, detect tables, split text ---
    final_chunks = []
    for doc in header_chunks:
        text = doc.page_content
        metadata = doc.metadata

        # Skip Table of Contents chunks
        if metadata.get("h2_header", "").lower() == "table of contents":
            continue
        lines = text.strip().split("\n")
        table_lines = [l for l in lines if l.strip().startswith("|")]

        if table_lines:
            table_text = "\n".join(table_lines)

            # Large table (more than 3 data rows) → split by row, prepend headers
            if len(table_lines) > 5:
                row_chunks = split_large_table(table_text)
                for row_chunk in row_chunks:
                    final_chunks.append({
                        "content": row_chunk,
                        "metadata": metadata,
                        "has_table": True
                    })

                # Keep the section's prose (text around the table) as ordinary chunks
                prose_lines = [l for l in lines if not l.strip().startswith("|")]
                if any(l.strip() and not l.lstrip().startswith("#") for l in prose_lines):
                    for chunk in text_splitter.split_text("\n".join(prose_lines).strip()):
                        final_chunks.append({
                            "content": chunk,
                            "metadata": metadata,
                            "has_table": False
                        })
            else:
                # Small table → keep whole
                final_chunks.append({
                    "content": text,
                    "metadata": metadata,
                    "has_table": True
                })
        else:
            sub_chunks = text_splitter.split_text(text)
            for chunk in sub_chunks:
                final_chunks.append({
                    "content": chunk,
                    "metadata": metadata,
                    "has_table": False
                })

    return final_chunks