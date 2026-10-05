import math

def simple_sieve(limit):
    """All primes up to limit via classic sieve. Deterministic ascending order."""
    if limit < 2:
        return []
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    for i in range(2, math.isqrt(limit) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]]


def segmented_sieve(L, R):
    """
    All primes in [L, R] via segmented sieve.
    Returns a list sorted in strictly increasing order (deterministic).
    """
    if L > R:
        return []
    if L < 2:
        L = 2
    if L > R:
        return []

    base_primes = simple_sieve(math.isqrt(R))
    size = R - L + 1
    is_prime = [True] * size

    for p in base_primes:
        start = max(p * p, ((L + p - 1) // p) * p)
        for m in range(start, R + 1, p):
            is_prime[m - L] = False

    # Ascending scan => deterministic ordering.
    return [L + i for i in range(size) if is_prime[i]]


def largest_prime_gap(L, R):
    """
    Largest gap between consecutive primes in [L, R].

    Tie handling (deterministic): if multiple consecutive-prime pairs share
    the maximum gap, return the FIRST such pair in ascending order of the
    smaller prime. Strict '>' implements this because `primes` is ascending.

    Returns:
        (gap, (p1, p2)) with gap an int > 0, or (None, None) if fewer than
        two primes exist in [L, R].
    """
    primes = segmented_sieve(L, R)

    # Degenerate case: need at least two primes to form a gap.
    if len(primes) < 2:
        return None, None

    max_gap = 0
    gap_pair = (None, None)

    # Strict '>' keeps the EARLIEST pair on ties -> deterministic.
    for i in range(1, len(primes)):
        gap = primes[i] - primes[i - 1]
        if gap > max_gap:
            max_gap = gap
            gap_pair = (primes[i - 1], primes[i])

    return max_gap, gap_pair


# ==================== Tests / Verification ====================
if __name__ == "__main__":
    # Defect case: tied maximum gap of 4 at (7,11) and (13,17).
    L, R = 5, 17
    gap, pair = largest_prime_gap(L, R)
    primes = segmented_sieve(L, R)
    print(f"[{L}, {R}] primes = {primes}")
    print(f"gap = {gap}, pair = {pair}")
    assert gap == 4
    assert pair == (7, 11), "Tie-break must pick the first pair ascending"

    # Degenerate cases (fewer than 2 primes)
    assert largest_prime_gap(1, 2) == (None, None)     # only {2}
    assert largest_prime_gap(8, 10) == (None, None)    # none
    assert largest_prime_gap(14, 16) == (None, None)   # none
    assert largest_prime_gap(20, 22) == (None, None)   # none

    # Unique max gap sanity checks
    assert largest_prime_gap(3, 11) == (4, (7, 11))
    assert largest_prime_gap(10, 50) == (6, (23, 29))

    # Wider range, just to confirm it still runs
    g, p = largest_prime_gap(999900, 1000000)
    print(f"wide range -> gap={g}, pair={p}")

    # Determinism check: same inputs, same outputs, repeated runs
    for _ in range(5):
        assert largest_prime_gap(5, 17) == (4, (7, 11))
        assert largest_prime_gap(999900, 1000000) == (g, p)

    print("All assertions passed.")