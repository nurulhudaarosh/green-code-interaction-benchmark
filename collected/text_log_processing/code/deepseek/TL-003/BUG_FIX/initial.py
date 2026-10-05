import os
from typing import Tuple

def dedup_lines(in_path: str, out_path: str, mode: str = 'exact') -> Tuple[int, int, int]:
    """
    Remove duplicate lines from a file, preserving first-occurrence order.
    
    Args:
        in_path: Path to the input file
        out_path: Path to the output file
        mode: Deduplication mode:
              - 'exact': exact line matching (default)
              - 'strip': compare lines after stripping whitespace
              - 'casefold': case-insensitive comparison
              - 'strip_casefold': strip whitespace + case-insensitive
    
    Returns:
        Tuple of (total_lines, unique_lines, removed_lines)
    
    Raises:
        ValueError: If mode is not one of the supported values
        FileNotFoundError: If input file doesn't exist
    """
    valid_modes = {'exact', 'strip', 'casefold', 'strip_casefold'}
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of {valid_modes}")
    
    if not os.path.isfile(in_path):
        raise FileNotFoundError(f"Input file not found: {in_path}")
    
    seen = set()
    total = 0
    unique = 0
    removed = 0
    
    # Use newline='' to preserve original line endings when writing
    with open(in_path, 'r', encoding='utf-8', newline='') as fin, \
         open(out_path, 'w', encoding='utf-8', newline='') as fout:
        
        for line in fin:
            total += 1
            
            # Normalize the line based on mode for comparison
            # Strip trailing newline characters for the key
            key_line = line.rstrip('\r\n')
            
            if mode == 'exact':
                key = key_line
            elif mode == 'strip':
                key = key_line.strip()
            elif mode == 'casefold':
                key = key_line.casefold()
            else:  # strip_casefold
                key = key_line.strip().casefold()
            
            if key in seen:
                removed += 1
            else:
                seen.add(key)
                fout.write(line)  # Preserve original line (incl. line ending)
                unique += 1
    
    return total, unique, removed


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input> <output> [mode]")
        sys.exit(1)
    
    mode = sys.argv[3] if len(sys.argv) > 3 else 'exact'
    total, unique, removed = dedup_lines(sys.argv[1], sys.argv[2], mode)
    print(f"Total: {total}, Unique: {unique}, Removed: {removed}")