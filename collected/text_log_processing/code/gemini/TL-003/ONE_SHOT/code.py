from pathlib import Path
from typing import Dict, Union


def dedup_lines(
    in_path: Union[str, Path],
    out_path: Union[str, Path],
    mode: str = 'exact'
) -> Dict[str, int]:
    """Stream an input file, deduplicate lines, and write first occurrences to an output file.
    
    Args:
        in_path: Path to the source file.
        out_path: Path to the target deduplicated file.
        mode: Comparison mode ('exact' or 'normalized').
        
    Returns:
        A dictionary with counts for 'total', 'unique', and 'removed' lines.
    """
    if mode not in ('exact', 'normalized'):
        raise ValueError(f"Unsupported mode: {mode!r}. Must be 'exact' or 'normalized'.")

    seen = set()
    total = 0
    unique = 0

    with open(in_path, 'r', encoding='utf-8') as src, \
         open(out_path, 'w', encoding='utf-8') as dst:
        for raw_line in src:
            total += 1

            # Strip only trailing line breaks (\r, \n) while preserving interior/leading spacing
            clean_line = raw_line.rstrip('\r\n')

            # Compute the deduplication key based on mode
            if mode == 'normalized':
                key = ' '.join(clean_line.strip().lower().split())
            else:
                key = clean_line

            if key not in seen:
                seen.add(key)
                unique += 1
                dst.write(clean_line + '\n')

    return {
        'total': total,
        'unique': unique,
        'removed': total - unique
    }