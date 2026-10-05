import re
import unicodedata
from collections import OrderedDict
from typing import Iterable, List, Tuple, Callable, Union


def _normalize(line: str) -> str:
    line = unicodedata.normalize("NFKC", line)
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    return line.casefold()


def _strip_line_ending(line: str) -> str:
    """Strip at most one trailing line ending (\\n, \\r\\n, or \\r)."""
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def dedup_lines(
    lines: Iterable[str],
    mode: str = "exact",
    keep: str = "first",
    return_counts: bool = True,
) -> Union[List[Tuple[str, int]], List[str]]:
    """Deduplicate lines while preserving order.

    Edge cases handled:
      * Empty input -> empty result.
      * Single line -> one entry with count 1.
      * All lines identical -> one entry with count == number of lines.
      * Trailing newlines (\\n, \\r\\n, \\r) are stripped per line.
      * Blank lines are deduplicated like any other line.
    """
    if mode not in ("exact", "normalized"):
        raise ValueError(f"mode must be 'exact' or 'normalized', got {mode!r}")
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    key_fn: Callable[[str], str] = (lambda s: s) if mode == "exact" else _normalize

    buckets: "OrderedDict[str, list]" = OrderedDict()

    for raw in lines:
        line = _strip_line_ending(raw)
        key = key_fn(line)
        bucket = buckets.get(key)
        if bucket is None:
            buckets[key] = [line, 1]
        else:
            bucket[1] += 1
            if keep == "last":
                bucket[0] = line

    if return_counts:
        return [(rep, count) for rep, count in buckets.values()]
    return [rep for rep, _ in buckets.values()]