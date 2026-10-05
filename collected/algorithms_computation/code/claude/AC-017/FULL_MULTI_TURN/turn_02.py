"""
Prime Range Analyzer

Problem: for integers L <= R, return (primes, largest_gap) where
  - primes      = ascending list of all primes in [L, R]
  - largest_gap = max difference between consecutive primes (0 if < 2 primes)

Rules:
  - Ties: the earliest pair (smallest lower prime) wins; this is used when the
    pair is reported and is checked in the self-tests below.
  - L > R is invalid and raises ValueError (no silent swapping).
  - L < 2 is clamped to 2 (no primes below 2).

Algorithm: base primes up to isqrt(R) via a simple sieve, then a segmented
sieve over [max(L, 2), R]. Standard library only, deterministic, no I/O
beyond argv/print.

Usage: python solution.py L R   (no args -> demo on [1, 100])
"""

import sys
from math import isqrt

BLOCK_SIZE = 1 << 20


def simple_sieve(n):
    """All primes <= n (sieve of Eratosthenes)."""
    if n < 2:
        return []
    flags = bytearray([1]) * (n + 1)
    flags[0] = flags[1] = 0
    for i in range(2, isqrt(n) + 1):
        if flags[i]:
            flags[i * i::i] = bytes(len(range(i * i, n + 1, i)))
    return [i for i in range(2, n + 1) if flags[i]]


def primes_in_range(L, R):
    """Sorted primes in [L, R] via segmented sieve. Requires L <= R."""
    if L > R:
        raise ValueError(f"invalid interval: L={L} > R={R}")
    lo = max(L, 2)
    if lo > R:
        return []
    base = simple_sieve(isqrt(R))
    result = []
    seg_lo = lo
    while seg_lo <= R:
        seg_hi = min(seg_lo + BLOCK_SIZE - 1, R)
        size = seg_hi - seg_lo + 1
        seg = bytearray([1]) * size
        for p in base:
            if p * p > seg_hi:
                break
            start = max(p * p, ((seg_lo + p - 1) // p) * p)
            if start > seg_hi:
                continue
            offset = start - seg_lo
            seg[offset::p] = bytes(len(range(offset, size, p)))
        result.extend(seg_lo + i for i in range(size) if seg[i])
        seg_lo = seg_hi + 1
    return result


def largest_gap_pair(primes):
    """Return (gap, (p, q)); on ties the EARLIEST pair wins (strict '>').
    Returns (0, None) when fewer than two primes."""
    best, pair = 0, None
    for a, b in zip(primes, primes[1:]):
        if b - a > best:
            best, pair = b - a, (a, b)
    return best, pair


def solve(L, R):
    """Exactly the required result: (primes, largest_gap)."""
    primes = primes_in_range(L, R)
    gap, _ = largest_gap_pair(primes)
    return primes, gap


def _self_test():
    assert solve(1, 100)[1] == 8
    assert solve(1, 20)[1] == 4
    assert largest_gap_pair(solve(1, 20)[0]) == (4, (7, 11))  # tie -> earliest
    assert solve(14, 16) == ([], 0)
    assert solve(13, 13) == ([13], 0)
    assert solve(-5, 2) == ([2], 0)
    assert solve(2, 3) == ([2, 3], 1)
    try:
        solve(100, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("L > R must raise ValueError")


def main():
    _self_test()
    if len(sys.argv) >= 3:
        L, R = int(sys.argv[1]), int(sys.argv[2])
    else:
        L, R = 1, 100
    primes, gap = solve(L, R)
    _, pair = largest_gap_pair(primes)
    print(f"Range: [{L}, {R}]")
    print(f"Prime count: {len(primes)}")
    print(f"Primes: {primes}")
    if pair is None:
        print("Largest gap: 0 (fewer than two primes)")
    else:
        print(f"Largest gap: {gap} (between {pair[0]} and {pair[1]})")


if __name__ == "__main__":
    main()