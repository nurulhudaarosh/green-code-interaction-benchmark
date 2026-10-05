from pathlib import Path
from typing import Dict, Union


def dedup_lines(
    in_path: Union[str, Path],
    out_path: Union[str, Path],
    mode: str = "exact",
) -> Dict[str, int]:
    """Streams an input file, deduplicates lines while preserving first-occurrence order,

    and writes them to an output file.

    Parameters:
        in_path: Path to the source file.
        out_path: Path to write the deduplicated output.
        mode: 'exact' (compares stripped of trailing newline) or
              'normalized' (compares lowercased and whitespace-collapsed).

    Returns:
        A dict containing counts: {'total': int, 'unique': int, 'removed': int}
    """
    if mode not in ("exact", "normalized"):
        raise ValueError(
            f"Invalid mode {mode!r}. Expected 'exact' or 'normalized'."
        )

    seen = set()
    total = 0
    unique = 0

    with open(in_path, "r", encoding="utf-8") as src, open(
        out_path, "w", encoding="utf-8"
    ) as dst:
        for raw_line in src:
            total += 1
            line = raw_line.rstrip("\r\n")

            if mode == "normalized":
                key = " ".join(line.strip().lower().split())
            else:
                key = line

            if key not in seen:
                seen.add(key)
                unique += 1
                dst.write(line + "\n")

    return {"total": total, "unique": unique, "removed": total - unique}