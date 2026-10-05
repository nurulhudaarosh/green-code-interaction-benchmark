if not (0 <= max_hamming <= hash_size ** 2):
    raise ValueError(
        f"max_hamming must be in [0, {hash_size ** 2}]"
    )