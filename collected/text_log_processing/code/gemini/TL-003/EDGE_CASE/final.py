from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
import os
from typing import Literal, Union


@dataclass(slots=True)
class LineEntry:
    line: str
    count: int = 1


def _default_normalizer(line: str) -> str:
    """Case-insensitive and whitespace-stripped normalization."""
    return line.strip().lower()


def dedup_lines(
    source: Union[Iterable[str], str, os.PathLike],
    *,
    mode: Literal["exact", "normalized"] = "exact",
    with_counts: bool = False,
    normalizer: Callable[[str], str] | None = None,
    keepends: bool = False,
    encoding: str = "utf-8",
) -> Iterator[str | tuple[str, int]]:
    """Deduplicate lines while preserving the order of their first appearance.

    Correctly handles:
      - Empty iterables / empty files (yields nothing).
      - Single-line inputs (yields single item or count of 1).
      - Identical repeated lines (yields single line with total count).

    Args:
        source: A file path, an iterable of strings, or a file-like object.
        mode: 'exact' or 'normalized'.
        with_counts: If True, yields `(line, count)`. If False, yields `line`.
        normalizer: Custom normalization callable for `mode='normalized'`.
        keepends: If True, retains newline characters (`\\n`, `\\r\\n`).
                  Defaults to False to prevent false duplicates across EOF.
        encoding: File encoding used when `source` is a path string/PathLike.

    Yields:
        Unique lines (or `(line, count)` tuples) in order of first appearance.
    """
    if mode == "exact":
        key_fn = lambda s: s
    elif mode == "normalized":
        key_fn = normalizer or _default_normalizer
    else:
        raise ValueError(f"Unknown mode: {mode!r}. Expected 'exact' or 'normalized'.")

    def _line_stream() -> Iterator[str]:
        """Normalize line generation across file paths, file objects, and sequences."""
        if isinstance(source, (str, os.PathLike)):
            if os.path.exists(source):
                with open(source, mode="r", encoding=encoding) as f:
                    for raw_line in f:
                        yield raw_line if keepends else raw_line.rstrip("\r\n")
                return
            else:
                # If it's a raw string that isn't an existing file path,
                # split lines instead of iterating character-by-character
                for raw_line in source.splitlines(keepends=keepends):
                    yield raw_line
                return

        for raw_line in source:
            yield raw_line if keepends else raw_line.rstrip("\r\n")

    lines = _line_stream()

    if with_counts:
        # Full aggregation pass
        seen: dict[str, LineEntry] = {}
        for line in lines:
            key = key_fn(line)
            if key not in seen:
                seen[key] = LineEntry(line=line, count=1)
            else:
                seen[key].count += 1

        for entry in seen.values():
            yield entry.line, entry.count
    else:
        # Lazy streaming pass
        seen_keys: set[str] = set()
        for line in lines:
            key = key_fn(line)
            if key not in seen_keys:
                seen_keys.add(key)
                yield line