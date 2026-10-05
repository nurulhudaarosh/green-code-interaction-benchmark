import os
import re
from typing import Tuple

# Split on any run of Unicode whitespace, then rejoin with a single space.
_WS_RUN = re.compile(r'\s+')

def _normalize_ws(s: str) -> str:
    """Collapse all internal whitespace runs to a single space and trim ends."""
    return _WS_RUN.sub(' ', s).strip()

def _strip_one_terminator(line: str) -> str:
    """
    Remove exactly one trailing line terminator from `line`, if present.
    Handles '\\n', '\\r\\n', and '\\r' (old Mac). Leaves other trailing
    whitespace/content intact.
    """
    if line.endswith('\r\n'):
        return line[:-2]
    if line.endswith('\n') or line.endswith('\r'):
        return line[:-1]
    return line

def dedup_lines(in_path: str, out_path: str, mode: str = 'exact') -> Tuple[int, int, int]:
    """
    Remove duplicate lines from a file, preserving first-occurrence order.

    Args:
        in_path: Path to the input file.
        out_path: Path to the output file.
        mode: Deduplication mode:
              - 'exact':         compare the raw line content (minus terminator)
              - 'strip':         trim leading/trailing whitespace only
              - 'casefold':      case-insensitive (Unicode-safe) on raw content
              - 'normalize':     collapse internal whitespace + trim + casefold
              - 'strip_casefold': trim + casefold (kept for backward-compat)

    Returns:
        (total_lines, unique_lines, removed_lines)

    Raises:
        ValueError: On an unsupported mode.
        FileNotFoundError: If the input file does not exist.
    """
    valid_modes = {'exact', 'strip', 'casefold', 'strip_casefold', 'normalize'}
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of {sorted(valid_modes)}")

    if not os.path.isfile(in_path):
        raise FileNotFoundError(f"Input file not found: {in_path}")

    seen = set()
    total = 0
    unique = 0
    removed = 0

    # newline='' => no universal-newline translation; we see the real terminator.
    with open(in_path, 'r', encoding='utf-8', newline='') as fin, \
         open(out_path, 'w', encoding='utf-8', newline='') as fout:

        for line in fin:
            total += 1
            content = _strip_one_terminator(line)

            if mode == 'exact':
                key = content
            elif mode == 'strip':
                key = content.strip()
            elif mode == 'casefold':
                key = content.casefold()
            elif mode == 'strip_casefold':
                key = content.strip().casefold()
            else:  # 'normalize'
                key = _normalize_ws(content).casefold()

            if key in seen:
                removed += 1
            else:
                seen.add(key)
                # Preserve the original line bytes, including its terminator.
                # If the last line lacked a terminator, it stays lacking one.
                fout.write(line)
                unique += 1

    return total, unique, removed