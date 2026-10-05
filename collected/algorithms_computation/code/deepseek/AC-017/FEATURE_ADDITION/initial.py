import math

def simple_sieve(limit):
    """Return list of primes up to limit using Sieve of Eratosthenes."""
    if limit < 2:
        return []
    sieve = bytearray(b'\x01') * (limit + 1)
    sieve[0:2] = b'\x00\x00'
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            start = i * i
            sieve[start:limit + 1:i] = b'\x00' * (((limit - start) // i) + 1)
    return [i for i in range(2, limit + 1) if sieve[i]]


def largest_prime_gap(L, R):
    """
    Return the largest gap between consecutive primes in [L, R].
    Returns None if there are fewer than 2 primes in the interval.
    """
    if R < 2:
        return None
    L = max(L, 2)

    # Base primes up to sqrt(R)
    limit = math.isqrt(R)
    base_primes = simple_sieve(limit)

    # Segmented sieve over [L, R]
    size = R - L + 1
    is_prime = bytearray(b'\x01') * size

    for p in base_primes:
        # First multiple of p >= L, but at least p*p
        start = max(p * p, ((L + p - 1) // p) * p)
        for multiple in range(start, R + 1, p):
            is_prime[multiple - L] = 0

    # Collect primes in [L, R]
    primes = [L + i for i in range(size) if is_prime[i]]

    if len(primes) < 2:
        return None

    # Find maximum gap
    max_gap = 0
    for i in range(1, len(primes)):
        gap = primes[i] - primes[i - 1]
        if gap > max_gap:
            max_gap = gap
    return max_gap


if __name__ == "__main__":
    L, R = 10, 50
    result = largest_prime_gap(L, R)
    if result is None:
        print(f"Fewer than 2 primes in [{L}, {R}] — no gap.")
    else:
        print(f"Largest prime gap in [{L}, {R}] = {result}")