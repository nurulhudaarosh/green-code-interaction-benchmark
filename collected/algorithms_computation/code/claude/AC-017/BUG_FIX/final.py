from math import isqrt


def _base_primes(n):
    """All primes <= n via a simple sieve."""
    if n < 2:
        return []
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, isqrt(n) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytes(len(range(i * i, n + 1, i)))
    return [i for i, v in enumerate(sieve) if v]


def primes_in_range(L, R, block=1 << 20):
    """Yield all primes in [L, R] in increasing order (segmented sieve)."""
    if R < 2 or L > R:
        return
    L = max(L, 2)
    base = _base_primes(isqrt(R))
    for lo in range(L, R + 1, block):
        hi = min(R, lo + block - 1)
        seg = bytearray([1]) * (hi - lo + 1)
        for p in base:
            if p * p > hi:
                break
            start = max(p * p, ((lo + p - 1) // p) * p)
            if start <= hi:
                seg[start - lo::p] = bytes(len(range(start - lo, hi - lo + 1, p)))
        i = seg.find(1)
        while i != -1:
            yield lo + i
            i = seg.find(1, i + 1)


def list_primes(L, R):
    """All primes in [L, R], ascending."""
    return list(primes_in_range(L, R))


def _scan_gaps(L, R):
    """Return (max_gap, first_pair) in one streaming pass.
    Strict '>' means ties keep the earliest pair. (0, None) if < 2 primes."""
    best_gap, best_pair, prev = 0, None, None
    for p in primes_in_range(L, R):
        if prev is not None and p - prev > best_gap:
            best_gap, best_pair = p - prev, (prev, p)
        prev = p
    return best_gap, best_pair


def largest_prime_gap(L, R):
    """Required result: the largest gap between consecutive primes in
    [L, R] as an int; 0 if the range has fewer than two primes."""
    return _scan_gaps(L, R)[0]


def largest_gap_pair(L, R):
    """Optional: the first (smallest) consecutive pair achieving the
    largest gap, or None if fewer than two primes."""
    return _scan_gaps(L, R)[1]


if __name__ == "__main__":
    for L, R in [(1, 100), (10, 20), (14, 16), (0, 1), (1, 10)]:
        print(f"[{L}, {R}] -> gap={largest_prime_gap(L, R)}, "
              f"pair={largest_gap_pair(L, R)}")