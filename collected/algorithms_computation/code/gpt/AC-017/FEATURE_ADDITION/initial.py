# Problem:
# Given an integer interval [L, R], list every prime number in that interval
# and return the largest gap between consecutive primes.
#
# Key constraints:
# - The interval width R - L is bounded, so a segmented sieve is practical.
# - Only the Python standard library is allowed.
# - No network access, APIs, external services, randomness, or human interaction.
# - The solution must be deterministic.
# - If fewer than two primes exist, the largest gap is 0.
#
# Required output:
# Return a dictionary:
# {
#     "primes": [all primes in [L, R] in ascending order],
#     "largest_gap": largest difference between consecutive primes, or 0
# }
#
# Algorithm:
# 1. Generate all base primes up to sqrt(R) using the ordinary sieve.
# 2. Create a boolean segment representing [L, R].
# 3. For every base prime p, mark its multiples inside the segment as composite.
#    The first multiple to mark is max(p*p, ceil(L/p) * p).
# 4. Extract the remaining prime values in ascending order.
# 5. Compute the largest difference between consecutive primes.

from math import isqrt


def generate_base_primes(limit: int) -> list[int]:
    """Generate all primes from 2 through limit using the Sieve of Eratosthenes."""
    if limit < 2:
        return []

    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False

    for p in range(2, isqrt(limit) + 1):
        if is_prime[p]:
            start = p * p
            is_prime[start:limit + 1:p] = [False] * (
                ((limit - start) // p) + 1
            )

    return [n for n, prime in enumerate(is_prime) if prime]


def prime_range_analyzer(L: int, R: int) -> dict:
    """
    Return all primes in [L, R] and the largest gap between
    consecutive primes.
    """
    if L > R:
        raise ValueError("L must be less than or equal to R.")

    # A prime cannot be smaller than 2.
    segment_start = max(L, 2)

    if segment_start > R:
        return {
            "primes": [],
            "largest_gap": 0,
        }

    # Generate base primes through sqrt(R).
    base_primes = generate_base_primes(isqrt(R))

    # Segmented sieve for [segment_start, R].
    size = R - segment_start + 1
    is_prime = [True] * size

    for p in base_primes:
        # Multiples below p*p may be prime themselves, so start at p*p.
        first_multiple = max(
            p * p,
            ((segment_start + p - 1) // p) * p
        )

        for multiple in range(first_multiple, R + 1, p):
            is_prime[multiple - segment_start] = False

    primes = [
        segment_start + i
        for i, prime in enumerate(is_prime)
        if prime
    ]

    largest_gap = 0
    for i in range(1, len(primes)):
        largest_gap = max(largest_gap, primes[i] - primes[i - 1])

    return {
        "primes": primes,
        "largest_gap": largest_gap,
    }


# Example tests
if __name__ == "__main__":
    print(prime_range_analyzer(10, 30))
    # {
    #     'primes': [11, 13, 17, 19, 23, 29],
    #     'largest_gap': 6
    # }

    print(prime_range_analyzer(2, 2))
    # {'primes': [2], 'largest_gap': 0}

    print(prime_range_analyzer(14, 16))
    # {'primes': [], 'largest_gap': 0}

    print(prime_range_analyzer(1, 10))
    # {'primes': [2, 3, 5, 7], 'largest_gap': 2}