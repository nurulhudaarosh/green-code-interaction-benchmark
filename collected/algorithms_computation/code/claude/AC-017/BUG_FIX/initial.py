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


def largest_prime_gap(L, R):
    """Return (max_gap, (p, q)) for consecutive primes in [L, R],
    or (0, None) if fewer than two primes exist."""
    best_gap, best_pair = 0, None
    prev = None
    for p in primes_in_range(L, R):
        if prev is not None and p - prev > best_gap:  # strict > keeps first tie
            best_gap, best_pair = p - prev, (prev, p)
        prev = p
    return best_gap, best_pair


if __name__ == "__main__":
    tests = [(1, 100), (10, 20), (14, 16), (0, 1), (1_000_000, 1_001_000)]
    for L, R in tests:
        print(f"[{L}, {R}] -> {largest_prime_gap(L, R)}")