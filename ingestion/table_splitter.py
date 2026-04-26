def split_large_table(table_text):
    lines = table_text.strip().split("\n")
    
    header = lines[0]      # | Destination | Daily Allowance |
    separator = lines[1]   # |-------------|-----------------|
    data_rows = lines[2:]  # everything after
    
    chunks = []
    for row in data_rows:
        chunks.append(f"{header}\n{separator}\n{row}")
        pass
    
    return chunks


# Test it
table = """| Destination | Daily Allowance |
|-------------|-----------------|
| USA         | $80             |
| Europe      | $70             |
| Asia        | $60             |"""

if __name__ == "__main__":
    result = split_large_table(table)
    for i, chunk in enumerate(result):
        print(f"--- Table Chunk {i+1} ---")
        print(chunk)
        print()