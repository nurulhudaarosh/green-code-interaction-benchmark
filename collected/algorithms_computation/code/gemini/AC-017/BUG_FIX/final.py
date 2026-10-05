import math
from typing import Tuple, Optional

def analyze_prime_range(L: int, R: int) -> Tuple[int, Optional[Tuple[int, int]]]:
    """
    Finds primes in range [L, R] using a Segmented Sieve.
    
    Returns:
        (max_gap, prime_pair) where:
        - max_gap is the integer max difference (0 if fewer than 2 primes exist).
        - prime_pair is a tuple (p1, p2) representing the FIRST occurrence 
          of two consecutive primes with the maximum gap, or None if max_gap == 0.
    """
    if R < 2 or L > R:
        return 0, None

    segment_low = max(2, L)
    segment_high = R

    if segment_low > segment_high:
        return 0, None

    # Step 1: Generate base primes up to floor(sqrt(R))
    limit = math.isqrt(segment_high)
    base_is_prime = [True] * (limit + 1)
    if limit >= 0:
        base_is_prime[0] = False
    if limit >= 1:
        base_is_prime[1] = False

    for i in range(2, math.isqrt(limit) + 1):
        if base_is_prime[i]:
            for j in range(i * i, limit + 1, i):
                base_is_prime[j] = False

    base_primes = [i for i, is_p in enumerate(base_is_prime) if is_p]

    # Step 2: Segmented Sieve on [segment_low, segment_high]
    range_len = segment_high - segment_low + 1
    is_prime_in_range = [True] * range_len

    for p in base_primes:
        # Smallest multiple of p that is >= segment_low and >= 2 * p
        start_multiple = max(p * p, ((segment_low + p - 1) // p) * p)
        for multiple in range(start_multiple, segment_high + 1, p):
            is_prime_in_range[multiple - segment_low] = False

    # Collect primes in range
    primes = [
        segment_low + i
        for i, is_p in enumerate(is_prime_in_range)
        if is_p
    ]

    # Step 3: Compute maximum gap with deterministic tie handling (first pair)
    if len(primes) < 2:
        return 0, None

    max_gap = 0
    best_pair = None

    for i in range(1, len(primes)):
        gap = primes[i] - primes[i - 1]
        # Strict inequality ensures we deterministically pick the FIRST pair in case of a tie
        if gap > max_gap:
            max_gap = gap
            best_pair = (primes[i - 1], primes[i])

    return max_gap, best_pair


# Verification on the example [2, 10]
if __name__ == "__main__":
    gap, pair = analyze_prime_range(2, 10)
    print(f"Range [2, 10] -> Max Gap: {gap}, First Pair: {pair}")
    # Output: Range [2, 10] -> Max Gap: 2, First Pair: (3, 5)