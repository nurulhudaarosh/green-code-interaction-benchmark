if not (r.size == g.size == b.size):
    raise ValueError(
        f"Size mismatch: R={r.size}, G={g.size}, B={b.size}"
    )