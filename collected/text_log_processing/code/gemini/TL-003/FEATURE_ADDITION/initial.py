from collections import Counter
from typing import Dict, Iterable, Tuple


def deduplicate_lines(
    input_lines: Iterable[str], output_path: str | None = None
) -> Tuple[list[str], Dict[str, int]]:
    """Removes exact duplicate lines in order of appearance.

    Args:
        input_lines: An iterable of strings (e.g., list of lines or an open
          file object).
        output_path: Optional path to write unique lines to disk.

    Returns:
        A tuple of (unique_lines, counts_dict), where:
          - unique_lines: List of strings preserving first-seen order.
          - counts_dict: Mapping of each unique line to its total occurrence
            count.
    """
    seen: set[str] = set()
    unique_lines: list[str] = []
    counts: Counter[str] = Counter()

    out_file = open(output_path, "w", encoding="utf-8") if output_path else None

    try:
        for raw_line in input_lines:
            # Preserve original line terminators or exact content
            counts[raw_line] += 1

            if raw_line not in seen:
                seen.add(raw_line)
                unique_lines.append(raw_line)
                if out_file:
                    out_file.write(raw_line)
    finally:
        if out_file:
            out_file.close()

    return unique_lines, dict(counts)