from pathlib import Path
from typing import Dict, Union


def dedup_lines(
    in_path: Union[str, Path],
    out_path: Union[str, Path],
    mode: str = "exact",
) -> Dict[str, int]:
    """Streams an input file, deduplicates lines while preserving first-occurrence order,
    and writes them to an output file with consistent trailing newlines.

    Parameters:
        in_path: Path to the input file.
        out_path: Path to the output file.
        mode: 'exact' (matches raw line content without line terminators) or
              'normalized' (matches lowercased, whitespace-collapsed content).

    Returns:
        Dict[str, int]: {'total': int, 'unique': int, 'removed': int}
    """
    if mode not in ("exact", "normalized"):
        raise ValueError(f"Invalid mode {mode!r}. Expected 'exact' or 'normalized'.")

    seen = set()
    total = 0
    unique = 0

    with open(in_path, "r", encoding="utf-8") as src, open(
        out_path, "w", encoding="utf-8", newline="\n"
    ) as dst:
        for raw_line in src:
            total += 1

            # Strip only the actual line terminator (CRLF, LF, or CR)
            # This preserves any trailing content spaces on lines without a newline
            if raw_line.endswith("\r\n"):
                line = raw_line[:-2]
            elif raw_line.endswith("\n") or raw_line.endswith("\r"):
                line = raw_line[:-1]
            else:
                line = raw_line

            # Determine duplicate detection key
            if mode == "normalized":
                # .split() without args automatically handles tabs, multiple spaces,
                # and trims edges; lower() normalizes casing
                key = " ".join(line.lower().split())
            else:
                key = line

            if key not in seen:
                seen.add(key)
                unique += 1
                dst.write(line + "\n")

    return {
        "total": total,
        "unique": unique,
        "removed": total - unique,
    }