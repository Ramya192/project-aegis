from ingestion.chunker import chunk_markdown_document

md = """
# Travel Policy

## International Per Diems
Employees get a daily allowance.

| Destination | Allowance |
|-------------|-----------|
| USA         | 80        |
| Europe      | 70        |
| Asia        | 60        |
| Australia   | 90        |
| Japan       | 75        |

## Ground Transportation
Taxis are reimbursable up to 50 dollars per trip. Uber and Lyft are acceptable.
Receipts must be submitted within 30 days of travel for all ground transportation claims.
"""

chunks = chunk_markdown_document(md)
for i, c in enumerate(chunks, 1):
    print(f"Chunk {i} | table={c['has_table']} | len={len(c['content'])}")
    print(f"  {c['content'][:80]}")
    print()
