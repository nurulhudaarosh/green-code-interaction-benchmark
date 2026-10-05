from collections import OrderedDict


def remove_duplicate_lines(text: str, show_counts: bool = True) -> str:
    """
    Remove duplicate lines while preserving first-occurrence order.
    
    Args:
        text: Input text with lines to deduplicate.
        show_counts: If True, append (n) to lines that appear more than once.
    
    Returns:
        Deduplicated text with optional counts.
    """
    lines = text.splitlines()
    
    # OrderedDict preserves insertion order (first occurrence order)
    counts = OrderedDict()
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    
    # Build output
    result = []
    for line, count in counts.items():
        if show_counts and count > 1:
            result.append(f"{line} ({count})")
        else:
            result.append(line)
    
    return "\n".join(result)


def remove_duplicate_lines_with_stats(text: str) -> dict:
    """
    Same as above but returns stats alongside the deduplicated text.
    """
    lines = text.splitlines()
    counts = OrderedDict()
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    
    output_lines = []
    for line, count in counts.items():
        output_lines.append(f"{line} ({count})" if count > 1 else line)
    
    total = len(lines)
    unique = len(counts)
    
    return {
        "output": "\n".join(output_lines),
        "total_lines": total,
        "unique_lines": unique,
        "duplicates_removed": total - unique,
        "counts": dict(counts),
    }


# ---------------- Example usage ----------------
if __name__ == "__main__":
    sample = """apple
banana
apple
cherry
banana
apple

final line
banana"""

    print("=== Simple output ===")
    print(remove_duplicate_lines(sample))
    # apple (3)
    # banana (3)
    # cherry
    # (empty line)
    # final line

    print("\n=== With stats ===")
    stats = remove_duplicate_lines_with_stats(sample)
    print(stats["output"])
    print(f"\nTotal lines:        {stats['total_lines']}")
    print(f"Unique lines:       {stats['unique_lines']}")
    print(f"Duplicates removed: {stats['duplicates_removed']}")
    print(f"Counts:             {stats['counts']}")