import re

_WS_RE = re.compile(r"\s+")


def _normalize(line):
    """Collapse internal whitespace, strip ends, lowercase."""
    return _WS_RE.sub(" ", line.strip()).lower()


def remove_duplicate_lines(lines, mode="exact"):
    """
    Remove duplicate lines while preserving order.

    Args:
        lines: An iterable of strings, or a single string with newlines.
        mode: 'exact'      -> compare raw lines
              'normalized' -> compare stripped, lowercased, whitespace-collapsed form

    Returns:
        tuple: (unique_lines, counts)
            - unique_lines: list of unique lines in original order
              (first-seen raw form is kept as the representative)
            - counts: dict mapping the *compared key* to its occurrence count
    """
    if isinstance(lines, str):
        lines = lines.splitlines()

    if mode not in ("exact", "normalized"):
        raise ValueError(f"unknown mode: {mode!r}")

    key_fn = (lambda s: s) if mode == "exact" else _normalize

    seen = set()
    unique_lines = []
    counts = {}

    for line in lines:
        key = key_fn(line)
        counts[key] = counts.get(key, 0) + 1
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)  # keep the first-seen raw line

    return unique_lines, counts


def dedupe_file(input_path, output_path, mode="exact"):
    with open(input_path) as f:
        unique, counts = remove_duplicate_lines(f.read().splitlines(), mode=mode)

    with open(output_path, "w") as f:
        f.write("\n".join(unique) + "\n")

    return counts


if __name__ == "__main__":
    sample = """Apple
  apple
banana
BANANA   
cherry\tpie
cherry   pie
date"""

    for mode in ("exact", "normalized"):
        unique, counts = remove_duplicate_lines(sample, mode=mode)
        print(f"--- mode={mode} ---")
        for line in unique:
            key = line if mode == "exact" else _normalize(line)
            print(f"  {line!r}  (x{counts[key]})")
        print()