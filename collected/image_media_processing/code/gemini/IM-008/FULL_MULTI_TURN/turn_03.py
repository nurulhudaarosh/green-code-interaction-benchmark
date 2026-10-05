import os
import hashlib
from collections import defaultdict

def find_exact_duplicates(input_dir, recursive=True):
    """
    Finds byte-identical files in `input_dir` by SHA-256 checksum.
    
    Args:
        input_dir (str): Root directory to search.
        recursive (bool): If True, search subdirectories. If False, top-level only.
        
    Returns:
        List[List[str]]: Duplicate path groups sorted alphabetically, relative to input_dir.
    """
    size_map = defaultdict(list)
    
    # Pass 1: Collect files relative to input_dir and group by file size
    if recursive:
        for root, _, files in os.walk(input_dir):
            for filename in files:
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, input_dir)
                try:
                    size = os.path.getsize(abs_path)
                    size_map[size].append((abs_path, rel_path))
                except (OSError, IOError):
                    continue
    else:
        try:
            for entry in os.scandir(input_dir):
                if entry.is_file(follow_symlinks=False):
                    rel_path = os.path.relpath(entry.path, input_dir)
                    try:
                        size = entry.stat().st_size
                        size_map[size].append((entry.path, rel_path))
                    except (OSError, IOError):
                        continue
        except (OSError, IOError):
            return []

    # Pass 2: Intermediate header check (first 1 KB) to discard non-matching candidates early
    header_map = defaultdict(list)
    for size, file_tuples in size_map.items():
        if len(file_tuples) < 2:
            continue
        for abs_path, rel_path in file_tuples:
            try:
                with open(abs_path, 'rb') as f:
                    header = f.read(1024)
                header_map[(size, header)].append((abs_path, rel_path))
            except (OSError, IOError):
                continue

    # Pass 3: Hash FULL file content for potential duplicate groups
    hash_map = defaultdict(list)
    CHUNK_SIZE = 64 * 1024  # Stream 64 KB chunks to EOF

    for file_tuples in header_map.values():
        if len(file_tuples) < 2:
            continue
            
        for abs_path, rel_path in file_tuples:
            try:
                hasher = hashlib.sha256()
                with open(abs_path, 'rb') as f:
                    while chunk := f.read(CHUNK_SIZE):
                        hasher.update(chunk)
                hash_map[hasher.hexdigest()].append(rel_path)
            except (OSError, IOError):
                continue

    # Return groups with 2+ exact byte matches, with relative paths sorted alphabetically
    return [sorted(paths) for paths in hash_map.values() if len(paths) >= 2]