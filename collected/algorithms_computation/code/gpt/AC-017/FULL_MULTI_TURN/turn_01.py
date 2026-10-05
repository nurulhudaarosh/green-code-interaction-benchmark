"""
Prime Range Analyzer

Problem:
    Given integers L and R, list every prime number in the inclusive interval
    [L, R], and return the largest gap between consecutive primes.

Key constraints:
    - L and R are integers with L <= R.
    - The interval width is bounded, so a segmented sieve is practical.
    - Only the Python standard library is used.
    - The solution is deterministic.
    - No network access, APIs, external services, randomness, or human
      interaction is required.

Required output:
    {
        "primes": [all primes in [L, R] in increasing order],
        "largest_gap": largest difference between consecutive primes
                       (0 if fewer than two primes exist)
    }

Algorithm:
    1. Generate all base primes up to sqrt(R) using the ordinary sieve.
    2. Create a boolean segmented sieve for [L, R].
    3. For every base prime p, mark its multiples in [L, R] as composite.
       The first multiple is max(p*p, ceil(L/p)*p).
    4. Collect the remaining numbers as primes.
    5. Compute the maximum difference between consecutive primes.

Complexity:
    Let W = R - L + 1 and B = sqrt(R).
    Base sieve: O(B log log B)
    Segmented sieve: approximately O(W log log R)
    Extra space: O(B + W)
"""

from math import isqrt


def _generate_base_primes(limit: int) -> list[int]:
    """Generate all primes from 2 through limit."""
    if limit < 2:
        return []

    composite = bytearray(limit + 1)
    primes = []

    for p in range(2, limit + 1):
        if composite[p] == 0:
            primes.append(p)

            # Start at p*p because smaller multiples were handled earlier.
            if p * p <= limit:
                composite[p * p : limit + 1 : p] = b"\x01" * (
                    ((limit - p * p) // p) + 1
                )

    return primes


def prime_range_analyzer(L: int, R: int) -> dict:
    """
    Return all primes in [L, R] and the largest gap between consecutive primes.

    Returns:
        {
            "primes": [...],
            "largest_gap": int
        }

    For an interval containing fewer than two primes, largest_gap is 0.
    """
    if not isinstance(L, int) or not isinstance(R, int):
        raise TypeError("L and R must be integers")

    if L > R:
        raise ValueError("L must be less than or equal to R")

    # No prime exists below 2.
    if R < 2:
        return {
            "primes": [],
            "largest_gap": 0,
        }

    start = max(L, 2)
    width = R - start + 1

    # Every number is initially considered prime.
    is_prime = bytearray(b"\x01") * width

    # Generate base primes through sqrt(R).
    base_primes = _generate_base_primes(isqrt(R))

    # Segmented sieve.
    for p in base_primes:
        # First multiple of p inside [start, R].
        first = max(p * p, ((start + p - 1) // p) * p)

        if first > R:
            continue

        # Convert the number to its index inside the segment.
        first_index = first - start
        count = ((width - 1 - first_index) // p) + 1

        is_prime[first_index::p] = b"\x00" * count

    primes = [
        start + i
        for i, value in enumerate(is_prime)
        if value
    ]

    largest_gap = 0
    for i in range(1, len(primes)):
        gap = primes[i] - primes[i - 1]
        if gap > largest_gap:
            largest_gap = gap

    return {
        "primes": primes,
        "largest_gap": largest_gap,
    }


# ------------------------------------------------------------
# Deterministic tests
# ------------------------------------------------------------

def _run_tests() -> None:
    # Normal interval.
    assert prime_range_analyzer(10, 30) == {
        "primes": [11, 13, 17, 19, 23, 29],
        "largest_gap": 6,
    }

    # Interval containing 2 and small primes.
    assert prime_range_analyzer(1, 10) == {
        "primes": [2, 3, 5, 7],
        "largest_gap": 2,
    }

    # Exactly one prime.
    assert prime_range_analyzer(11, 11) == {
        "primes": [11],
        "largest_gap": 0,
    }

    # No primes.
    assert prime_range_analyzer(14, 16) == {
        "primes": [],
        "largest_gap": 0,
    }

    # Interval entirely below the first prime.
    assert prime_range_analyzer(-10, 1) == {
        "primes": [],
        "largest_gap": 0,
    }

    # Interval starting at 2.
    assert prime_range_analyzer(2, 20) == {
        "primes": [2, 3, 5, 7, 11, 13, 17, 19],
        "largest_gap": 4,
    }

    # Repeated deterministic boundary check.
    expected = {
        "primes": [97],
        "largest_gap": 0,
    }
    assert prime_range_analyzer(97, 97) == expected
    assert prime_range_analyzer(97, 97) == expected

    # Invalid interval.
    try:
        prime_range_analyzer(20, 10)
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # Invalid types.
    try:
        prime_range_analyzer(2.0, 10)
        assert False, "Expected TypeError"
    except TypeError:
        pass


if __name__ == "__main__":
    _run_tests()
    print(prime_range_analyzer(10, 30))