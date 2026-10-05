"""
Prime Range Analyzer

Original problem:
    Given an integer interval [L, R], list every prime number in that
    inclusive range and return the largest gap between consecutive primes.

Original required output:
    {
        "primes": [...],       # all primes in [L, R], increasing
        "largest_gap": number  # largest consecutive-prime gap
    }

Rules:
    - The interval is inclusive.
    - Use a segmented sieve because the interval width is bounded.
    - Generate base primes through sqrt(R).
    - Preserve deterministic ordering.
    - If fewer than two primes exist, largest_gap is 0.
    - If the interval contains no primes, return an empty prime list
      and largest_gap = 0.
    - Reversed/empty intervals are handled deterministically as empty.
    - No changes are made to the original output fields or tie handling.

Difficult valid cases explicitly handled:
    1. Smallest permitted input:
       [2, 2] -> [2], largest_gap = 0
    2. Empty prime structure:
       [0, 1] or any interval containing no primes -> [] and 0
    3. Disconnected prime structure:
       A range with several separated primes, including large gaps,
       still returns every prime and the maximum consecutive gap.
    4. Intervals containing values below 2 are handled correctly.
    5. Reversed intervals are treated as empty.
"""

from math import isqrt


def prime_range_analyzer(L: int, R: int) -> dict:
    """
    Return all primes in [L, R] and the largest gap between
    consecutive primes.
    """

    # Empty/reversed interval.
    if L > R:
        return {
            "primes": [],
            "largest_gap": 0,
        }

    # No prime can exist when R < 2.
    if R < 2:
        return {
            "primes": [],
            "largest_gap": 0,
        }

    # ---------------------------------------------------------
    # 1. Generate base primes through sqrt(R)
    # ---------------------------------------------------------
    limit = isqrt(R)

    base_is_prime = [True] * (limit + 1)

    if limit >= 0:
        base_is_prime[0] = False
    if limit >= 1:
        base_is_prime[1] = False

    p = 2
    while p * p <= limit:
        if base_is_prime[p]:
            for multiple in range(p * p, limit + 1, p):
                base_is_prime[multiple] = False
        p += 1

    base_primes = [
        number
        for number in range(2, limit + 1)
        if base_is_prime[number]
    ]

    # ---------------------------------------------------------
    # 2. Segmented sieve over [max(L, 2), R]
    # ---------------------------------------------------------
    start = max(L, 2)
    width = R - start + 1

    if width <= 0:
        return {
            "primes": [],
            "largest_gap": 0,
        }

    is_prime = [True] * width

    for p in base_primes:
        # First multiple of p inside [start, R].
        # p*p prevents marking p itself as composite.
        first_multiple = max(
            p * p,
            ((start + p - 1) // p) * p
        )

        if first_multiple > R:
            continue

        for multiple in range(first_multiple, R + 1, p):
            is_prime[multiple - start] = False

    primes = [
        start + index
        for index, flag in enumerate(is_prime)
        if flag
    ]

    # ---------------------------------------------------------
    # 3. Find largest consecutive-prime gap
    # ---------------------------------------------------------
    largest_gap = 0

    for i in range(1, len(primes)):
        gap = primes[i] - primes[i - 1]
        if gap > largest_gap:
            largest_gap = gap

    return {
        "primes": primes,
        "largest_gap": largest_gap,
    }


# =============================================================
# Tests
# =============================================================

if __name__ == "__main__":

    # ---------------------------------------------------------
    # Original normal case
    # ---------------------------------------------------------
    assert prime_range_analyzer(10, 30) == {
        "primes": [11, 13, 17, 19, 23, 29],
        "largest_gap": 6,
    }

    # ---------------------------------------------------------
    # Difficult case 1:
    # Smallest permitted input: [2, 2]
    # ---------------------------------------------------------
    assert prime_range_analyzer(2, 2) == {
        "primes": [2],
        "largest_gap": 0,
    }

    # ---------------------------------------------------------
    # Difficult case 2:
    # Empty/disconnected prime structure.
    # [0, 1] contains no primes.
    # ---------------------------------------------------------
    assert prime_range_analyzer(0, 1) == {
        "primes": [],
        "largest_gap": 0,
    }

    # ---------------------------------------------------------
    # Empty prime structure with a larger valid interval.
    # ---------------------------------------------------------
    assert prime_range_analyzer(14, 16) == {
        "primes": [],
        "largest_gap": 0,
    }

    # ---------------------------------------------------------
    # Difficult case 3:
    # Values below 2 mixed with valid primes.
    # ---------------------------------------------------------
    assert prime_range_analyzer(-10, 10) == {
        "primes": [2, 3, 5, 7],
        "largest_gap": 2,
    }

    # ---------------------------------------------------------
    # Difficult case 4:
    # Disconnected primes with a large gap.
    # Consecutive primes in this range are:
    # 23, 29, 31, 37, 41, 43, 47
    # Largest gap = 6.
    # ---------------------------------------------------------
    assert prime_range_analyzer(23, 47) == {
        "primes": [23, 29, 31, 37, 41, 43, 47],
        "largest_gap": 6,
    }

    # ---------------------------------------------------------
    # Only one prime -> no consecutive pair.
    # ---------------------------------------------------------
    assert prime_range_analyzer(14, 17) == {
        "primes": [17],
        "largest_gap": 0,
    }

    # ---------------------------------------------------------
    # Reversed/empty interval.
    # ---------------------------------------------------------
    assert prime_range_analyzer(20, 10) == {
        "primes": [],
        "largest_gap": 0,
    }

    # ---------------------------------------------------------
    # Smallest range below the smallest prime.
    # ---------------------------------------------------------
    assert prime_range_analyzer(-5, 1) == {
        "primes": [],
        "largest_gap": 0,
    }

    # ---------------------------------------------------------
    # Larger disconnected structure.
    # Verifies that primes are returned in increasing order
    # and the maximum gap is computed from adjacent primes only.
    # ---------------------------------------------------------
    assert prime_range_analyzer(2, 50) == {
        "primes": [
            2, 3, 5, 7, 11, 13, 17, 19,
            23, 29, 31, 37, 41, 43, 47
        ],
        "largest_gap": 6,
    }

    print("All tests passed.")