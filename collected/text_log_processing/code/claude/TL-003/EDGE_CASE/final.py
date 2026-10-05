import re
import sys
from typing import Callable, Iterable, Optional

_WS = re.compile(r"\s+")


def _normalize(line: str) -> str:
    """Strip, collapse inner whitespace, case-insensitive."""
    return _WS.sub(" ", line.strip()).casefold()


def dedup_lines(
    lines: Iterable[str],
    mode: str = "exact",
    normalizer: Optional[Callable[[str], str]] = None,
) -> tuple[list[str], list[int]]:
    """
    Remove duplicate lines, preserving first-occurrence order.

    mode="exact":      lines are duplicates only if identical.
    mode="normalized": lines are duplicates if equal after strip,
                       whitespace collapse and casefold (or a custom
                       `normalizer`).

    Returns (unique_lines, counts); counts[i] is how many times
    unique_lines[i] occurred in the input (including the first).
    The first-seen original text is the one kept.
    """
    if mode == "exact":
        key = lambda s: s
    elif mode == "normalized":
        key = normalizer or _normalize
    else:
        raise ValueError(f"mode must be 'exact' or 'normalized', got {mode!r}")

    index: dict[str, int] = {}
    unique: list[str] = []
    counts: list[int] = []

    for line in lines:
        k = key(line)
        i = index.get(k)
        if i is None:
            index[k] = len(unique)
            unique.append(line)
            counts.append(1)
        else:
            counts[i] += 1

    return unique, counts


def dedup_text(text: str, mode: str = "exact") -> tuple[str, list[int]]:
    """Convenience wrapper for a multi-line string."""
    unique, counts = dedup_lines(text.splitlines(), mode)
    return "\n".join(unique), counts


if __name__ == "__main__":
    # Usage: python dedup_lines.py [exact|normalized] [-c] < input.txt
    args = sys.argv[1:]
    show_counts = "-c" in args
    mode = next((a for a in args if a in ("exact", "normalized")), "exact")

    unique, counts = dedup_lines((l.rstrip("\r\n") for l in sys.stdin), mode)
    for line, n in zip(unique, counts):
        print(f"{n:>6} {line}" if show_counts else line)