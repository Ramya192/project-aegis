from langchain_text_splitters import MarkdownHeaderTextSplitter

if __name__ == "__main__":

    markdown_text = """
# Corporate Travel Policy

## International Per Diems 
Employees travelling internationally are entitled to a daily allowance.
The allowance covers meals and incidentals.

## Ground Transportation
Taxis and rideshares are reimbursable up to $50 per trip.
Uber and Lyft are both acceptable.
"""
    headers_to_split_on = [
        ('#', "h1_header"),
        ('##', "h2_header"),
        ("###", "h3_header")
    ]

    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    chunks = splitter.split_text(markdown_text)

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk{i+1} ---")
        print("Content:", chunk.page_content)
        print("Metadata:", chunk.metadata)
        print()

    markdown_text1 = """
# Corporate Travel Policy

## International Per Diems
Employees are entitled to a daily allowance based on destination.

| Destination | Daily Allowance |
|-------------|-----------------|
| USA         | $80             |
| Europe      | $70             |
| Asia        | $60             |

## Ground Transportation
Taxis and rideshares are reimbursable up to $50 per trip.
"""
    headers_to_split_on1 = [
        ('#', "h1_header"),
        ('##', "h2_header"),
        ("###", "h3_header")
    ]

    splitter1 = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on1)
    chunks1 = splitter1.split_text(markdown_text1)

    for i, chunk in enumerate(chunks1):
        print(f"--- Chunk{i+1} ---")
        print("Content:", chunk.page_content)
        print("Metadata:", chunk.metadata)
        print()