def split_large_table(table_text: str) -> list[str]:
    """Split a Markdown table into one chunk per data row, each repeating the header rows."""
    lines = table_text.strip().split("\n")

    header = lines[0]      # | Destination | Daily Allowance |
    separator = lines[1]   # |-------------|-----------------|
    data_rows = lines[2:]

    return [f"{header}\n{separator}\n{row}" for row in data_rows]
