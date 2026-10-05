import os
import hashlib
from collections import defaultdict

def find_exact_duplicates(input_dir):
    """
    Finds byte-identical files in `input_dir` and its subdirectories by hashing 
    their FULL file content with SHA-256.
    """
    size_map = defaultdict(list)
    
    # Pass 1: Group by file size (fastest filter)
    for root, _, files in os.walk(input_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                size = os.path.getsize(filepath)
                size_map[size].append(filepath)
            except (OSError, IOError):
                continue

    # Pass 2: Optional optimization - check first 1 KB to quickly separate non-matching headers
    header_map = defaultdict(list)
    for size, paths in size_map.items():
        if len(paths) < 2:
            continue
        for path in paths:
            try:
                with open(path, 'rb') as f:
                    header = f.read(1024)
                header_map[(size, header)].append(path)
            except (OSError, IOError):
                continue

    # Pass 3: Hash FULL file content for groups sharing size and header
    hash_map = defaultdict(list)
    CHUNK_SIZE = 64 * 1024  # Stream 64 KB chunks through SHA-256 until EOF

    for paths in header_map.values():
        if len(paths) < 2:
            continue
            
        for path in paths:
            try:
                hasher = hashlib.sha256()
                with open(path, 'rb') as f:
                    # Continues reading until f.read() returns empty bytes (EOF)
                    while chunk := f.read(CHUNK_SIZE):
                        hasher.update(chunk)
                hash_map[hasher.hexdigest()].append(path)
            except (OSError, IOError):
                continue

    # Collect groups with 2+ exact byte matches and sort paths alphabetically
    return [sorted(paths) for paths in hash_map.values() if len(paths) >= 2]