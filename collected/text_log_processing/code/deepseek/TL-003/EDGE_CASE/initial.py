import re
import unicodedata
from collections import OrderedDict
from typing import Iterable, List, Tuple, Callable


def _normalize(line: str) -> str:
    """Normalize a line for comparison purposes.

    - Unicode NFKC normalization (folds compatibility forms)
    - Strip leading/trailing whitespace
    - Collapse internal whitespace runs to a single space
    - Lowercase
    """
    line = unicodedata.normalize("NFKC", line)
    line = line.strip()
    line = re.sub(r"\s+", " ", line)
    return line.casefold()


def dedup_lines(
    lines: Iterable[str],
    mode: str = "exact",
    keep: str = "first",
    return_counts: bool = True,
) -> List[Tuple[str, int]] | List[str]:
    """Deduplicate lines while preserving order.

    Args:
        lines: Iterable of strings (newlines are not required; if present,
            each element is treated as one line).
        mode: "exact" for byte-for-byte comparison, "normalized" for
            case-insensitive, whitespace-insensitive, Unicode-normalized
            comparison.
        keep: Which occurrence to keep as the representative line:
            "first" (default) or "last".
        return_counts: If True, return list of (line, count) tuples.
            If False, return list of unique lines only.

    Returns:
        If return_counts is True: list of (representative_line, count) in
        first-seen order of each key.
        If return_counts is False: list of representative lines.

    Raises:
        ValueError: For unknown mode or keep values.
    """
    if mode not in ("exact", "normalized"):
        raise ValueError(f"mode must be 'exact' or 'normalized', got {mode!r}")
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    if mode == "exact":
        key_fn: Callable[[str], str] = lambda s: s
    else:
        key_fn = _normalize

    # OrderedDict maps key -> [representative_line, count]
    buckets: "OrderedDict[str, list]" = OrderedDict()

    for line in lines:
        # Strip a single trailing newline if present, so callers can pass
        # either splitlines() output or a file iterated directly.
        if line.endswith("\n"):
            line = line[:-1]
            if line.endswith("\r"):
                line = line[:-1]

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