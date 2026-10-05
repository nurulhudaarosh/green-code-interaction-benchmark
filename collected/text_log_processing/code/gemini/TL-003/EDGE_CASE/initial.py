from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class LineEntry:
    line: str
    count: int = 1


def _default_normalizer(line: str) -> str:
    """Case-insensitive and whitespace-stripped normalization."""
    return line.strip().lower()


def dedup_lines(
    lines: Iterable[str],
    *,
    mode: Literal["exact", "normalized"] = "exact",
    with_counts: bool = False,
    normalizer: Callable[[str], str] | None = None,
) -> Iterator[str | tuple[str, int]]:
    """Deduplicate lines while preserving the order of their first appearance.

    Args:
        lines: An iterable of strings.
        mode: Deduplication strategy:
            - 'exact': Matches lines character-for-character.
            - 'normalized': Matches lines using a normalizer function.
        with_counts: If True, yields `(line, count)` tuples.
                     If False, yields `line` strings.
        normalizer: Custom normalization callable. If None and mode='normalized',
                    defaults to `line.strip().lower()`.

    Yields:
        Unique lines (or `(line, count)` tuples) in the order first encountered.
    """
    if mode == "exact":
        key_fn = lambda s: s
    elif mode == "normalized":
        key_fn = normalizer or _default_normalizer
    else:
        raise ValueError(f"Unknown mode: {mode!r}. Expected 'exact' or 'normalized'.")

    # Python 3.7+ dict preserves insertion order
    seen: dict[str, LineEntry] = {}

    if with_counts:
        # Full scan is necessary to compute total occurrences
        for line in lines:
            key = key_fn(line)
            if key not in seen:
                seen[key] = LineEntry(line=line, count=1)
            else:
                seen[key].count += 1

        for entry in seen.values():
            yield entry.line, entry.count

    else:
        # Stream unique lines immediately without buffering everything first
        seen_keys: set[str] = set()
        for line in lines:
            key = key_fn(line)
            if key not in seen_keys:
                seen_keys.add(key)
                yield line