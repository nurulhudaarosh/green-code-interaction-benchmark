from math import isqrt


def simple_sieve(n):
    """Return all primes <= n using a basic sieve of Eratosthenes."""
    if n < 2:
        return []
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, isqrt(n) + 1):
        if sieve[i]:
            sieve[i * i::i] = bytearray(len(range(i * i, n + 1, i)))
    return [i for i in range(2, n + 1) if sieve[i]]


def primes_in_range(L, R):
    """Return the sorted list of primes p with L <= p <= R (segmented sieve)."""
    L = max(L, 2)
    if L > R:
        return []

    base_primes = simple_sieve(isqrt(R))
    size = R - L + 1
    segment = bytearray([1]) * size  # segment[i] represents the number L + i

    for p in base_primes:
        # First multiple of p that is >= L, but never below p*p
        start = max(p * p, ((L + p - 1) // p) * p)
        if start > R:
            continue
        segment[start - L::p] = bytearray(len(range(start - L, size, p)))

    return [L + i for i in range(size) if segment[i]]


def largest_prime_gap(L, R):
    """
    Return (max_gap, (p, q), primes) where p < q are consecutive primes in
    [L, R] with q - p == max_gap (first such pair). If fewer than two primes
    exist, returns (0, None, primes).
    """
    primes = primes_in_range(L, R)
    if len(primes) < 2:
        return 0, None, primes

    best_gap = 0
    best_pair = None
    for a, b in zip(primes, primes[1:]):
        gap = b - a
        if gap > best_gap:
            best_gap = gap
            best_pair = (a, b)
    return best_gap, best_pair, primes


if __name__ == "__main__":
    tests = [
        (1, 30),        # primes: 2 3 5 7 11 13 17 19 23 29 -> gap 6 (23, 29)
        (90, 100),      # only 97 -> gap 0
        (14, 16),       # no primes -> gap 0
        (2, 2),         # single prime
        (100, 130),     # 101 103 107 109 113 127 131? (131 > 130) -> gap 14 (113, 127)
        (10**12, 10**12 + 1000),
    ]
    for L, R in tests:
        gap, pair, primes = largest_prime_gap(L, R)
        shown = primes if len(primes) <= 12 else f"{len(primes)} primes"
        print(f"[{L}, {R}] -> gap={gap}, pair={pair}, primes={shown}")