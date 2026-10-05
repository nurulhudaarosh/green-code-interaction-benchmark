def remove_duplicate_lines(lines):
    """
    Remove exact duplicate lines while preserving order.
    
    Args:
        lines: An iterable of strings (or a string with newlines)
    
    Returns:
        tuple: (unique_lines, counts)
            - unique_lines: list of unique lines in original order
            - counts: dict mapping each line to its occurrence count
    """
    # Allow passing a single string with newlines
    if isinstance(lines, str):
        lines = lines.splitlines()
    
    seen = set()
    unique_lines = []
    counts = {}
    
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
        if line not in seen:
            seen.add(line)
            unique_lines.append(line)
    
    return unique_lines, counts


if __name__ == "__main__":
    sample = """apple
banana
apple
cherry
banana
apple
date"""

    unique, counts = remove_duplicate_lines(sample)
    
    print("Unique lines (in order):")
    for line in unique:
        print(f"  {line}  (x{counts[line]})")
    
    print("\nCounts:", counts)