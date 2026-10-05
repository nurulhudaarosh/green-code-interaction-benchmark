import math

def simple_sieve(limit):
    """Return all primes <= limit using a basic sieve of Eratosthenes."""
    if limit < 2:
        return []
    sieve = bytearray([1]) * (limit + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            step = i
            start = i * i
            sieve[start:limit + 1:step] = b'\x00' * (((limit - start) // step) + 1)
    return [i for i in range(2, limit + 1) if sieve[i]]


def largest_prime_gap(L, R):
    """
    Return the largest gap between consecutive primes in [L, R].
    Returns None if fewer than 2 primes exist in the interval.
    """
    if R < 2 or L > R:
        return None

    # Base primes up to sqrt(R)
    limit = int(math.isqrt(R))
    base_primes = simple_sieve(limit)

    # Segmented sieve over [L, R]
    size = R - L + 1
    is_prime = bytearray([1]) * size

    # Handle 0 and 1 explicitly
    if L == 0:
        is_prime[0] = 0
        if size > 1:
            is_prime[1] = 0
    elif L == 1:
        is_prime[0] = 0

    for p in base_primes:
        # First multiple of p >= L, but at least p*p (optimization)
        start = max(p * p, ((L + p - 1) // p) * p)
        if start > R:
            continue
        # Mark multiples of p as composite
        for multiple in range(start, R + 1, p):
            is_prime[multiple - L] = 0

    # Collect primes and compute gaps
    prev = None
    max_gap = None
    for i in range(size):
        if is_prime[i]:
            current = L + i
            if prev is not None:
                gap = current - prev
                if max_gap is None or gap > max_gap:
                    max_gap = gap
            prev = current

    return max_gap


# ---- Example usage ----
if __name__ == "__main__":
    tests = [
        (1, 10),          # primes: 2,3,5,7     -> gaps: 1,2,2 -> max 2
        (10, 30),         # primes: 11,13,17,19,23,29 -> gaps: 2,4,2,4,6 -> max 6
        (0, 2),           # primes: 2 -> fewer than 2 -> None
        (14, 16),         # no primes -> None
        (100, 200),       # check manually if needed
        (10**9, 10**9 + 1000),  # large L, small segment
    ]
    for L, R in tests:
        print(f"[{L}, {R}] -> largest gap = {largest_prime_gap(L, R)}")