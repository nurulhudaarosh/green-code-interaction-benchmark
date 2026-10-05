from collections import OrderedDict


def remove_duplicate_lines(
    text: str,
    show_counts: bool = True,
    strip_whitespace: bool = False,
    ignore_empty: bool = False,
    preserve_trailing_newline: bool = True,
) -> str:
    """
    Remove duplicate lines while preserving first-occurrence order.

    Args:
        text: Input text.
        show_counts: Append (n) to lines that appear more than once.
        strip_whitespace: Strip leading/trailing whitespace before comparison.
            The stripped form is what gets output and counted.
        ignore_empty: Drop lines that are empty after optional stripping.
        preserve_trailing_newline: If the input ended with a newline, keep one
            on the output. Otherwise, don't add one.

    Returns:
        Deduplicated text.
    """
    # ---- 1. Detect trailing newline BEFORE splitting ----
    # str.splitlines() swallows the final newline, which would cause us to
    # silently drop it. Track it explicitly.
    ends_with_newline = text.endswith(("\n", "\r"))

    # ---- 2. Split into lines (handles \n, \r\n, \r) ----
    lines = text.splitlines()

    # Edge case: empty string. splitlines() -> []. Return "" (or "\n" if
    # user passed just a newline, which is one empty line).
    if not lines:
        return "\n" if (ends_with_newline and preserve_trailing_newline) else ""

    # ---- 3. Normalize each line ----
    def normalize(line: str) -> str:
        return line.strip() if strip_whitespace else line

    normalized = [normalize(l) for l in lines]

    if ignore_empty:
        normalized = [l for l in normalized if l != ""]

    # ---- 4. Count with first-occurrence order preserved ----
    counts: "OrderedDict[str, int]" = OrderedDict()
    for line in normalized:
        counts[line] = counts.get(line, 0) + 1

    # ---- 5. Build output ----
    out_lines = [
        f"{line} ({n})" if (show_counts and n > 1) else line
        for line, n in counts.items()
    ]

    result = "\n".join(out_lines)

    # ---- 6. Restore trailing newline if the input had one ----
    if preserve_trailing_newline and ends_with_newline and result:
        result += "\n"

    return result


def remove_duplicate_lines_with_stats(text: str, **kwargs) -> dict:
    """Same as above but returns stats alongside the deduplicated text."""
    ends_with_newline = text.endswith(("\n", "\r"))
    lines = text.splitlines()
    strip = kwargs.get("strip_whitespace", False)
    ignore_empty = kwargs.get("ignore_empty", False)

    normalized = [(l.strip() if strip else l) for l in lines]
    if ignore_empty:
        normalized = [l for l in normalized if l != ""]

    counts: "OrderedDict[str, int]" = OrderedDict()
    for line in normalized:
        counts[line] = counts.get(line, 0) + 1

    show_counts = kwargs.get("show_counts", True)
    out_lines = [
        f"{line} ({n})" if (show_counts and n > 1) else line
        for line, n in counts.items()
    ]
    result = "\n".join(out_lines)
    if kwargs.get("preserve_trailing_newline", True) and ends_with_newline and result:
        result += "\n"

    return {
        "output": result,
        "total_lines": len(normalized),
        "unique_lines": len(counts),
        "duplicates_removed": len(normalized) - len(counts),
        "counts": dict(counts),
        "had_trailing_newline": ends_with_newline,
    }


# ---------------- Example usage ----------------
if __name__ == "__main__":
    # Bug 1: missing trailing newline
    # Old code lost the final newline. New code preserves it.
    a = "apple\nbanana\napple\n"
    b = "apple\nbanana\napple"           # <-- no trailing \n
    print(repr(remove_duplicate_lines(a)))  # 'apple (2)\nbanana\n'
    print(repr(remove_duplicate_lines(b)))  # 'apple (2)\nbanana'

    # Bug 2: whitespace was treated as distinct
    messy = "apple\n  apple  \napple\t\n banana\nbanana "
    print("\n--- Whitespace-aware (strip) ---")
    print(remove_duplicate_lines(messy, strip_whitespace=True))
    # apple (3)
    # banana (2)

    print("\n--- Whitespace-preserving (default) ---")
    print(remove_duplicate_lines(messy))
    # apple
    #   apple  
    # apple\t
    #  banana
    # banana

    # Bug 3: blank lines counted as duplicates / broke ordering
    blanks = "a\n\n\nb\n\na\n"
    print("\n--- Empty lines preserved ---")
    print(repr(remove_duplicate_lines(blanks)))
    # 'a (2)\n\nb\n'

    print("\n--- Empty lines dropped ---")
    print(repr(remove_duplicate_lines(blanks, ignore_empty=True)))
    # 'a (2)\nb\n'