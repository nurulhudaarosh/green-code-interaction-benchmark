import math

def simple_sieve(limit):
    """Return list of primes up to limit using Sieve of Eratosthenes."""
    if limit < 2:
        return []
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(limit**0.5) + 1):
        if is_prime[i]:
            is_prime[i*i : limit+1 : i] = bytearray(len(range(i*i, limit+1, i)))
    return [i for i in range(2, limit + 1) if is_prime[i]]

def segmented_sieve_primes(L, R):
    """Return list of primes in [L, R] using segmented sieve."""
    if R < 2 or L > R:
        return []
    L = max(L, 2)  # no primes below 2
    
    limit = int(math.isqrt(R)) + 1
    base_primes = simple_sieve(limit)
    
    size = R - L + 1
    is_prime = bytearray([1]) * size
    
    for p in base_primes:
        # Find the first multiple of p >= L
        start = max(p * p, ((L + p - 1) // p) * p)
        for multiple in range(start, R + 1, p):
            is_prime[multiple - L] = 0
    
    return [L + i for i in range(size) if is_prime[i]]

def largest_prime_gap(L, R):
    """Return the largest gap between consecutive primes in [L, R].
    Returns (gap, prime1, prime2) or None if fewer than 2 primes."""
    primes = segmented_sieve_primes(L, R)
    if len(primes) < 2:
        return None
    
    max_gap = 0
    gap_pair = (None, None)
    for i in range(1, len(primes)):
        gap = primes[i] - primes[i-1]
        if gap > max_gap:
            max_gap = gap
            gap_pair = (primes[i-1], primes[i])
    
    return (max_gap, gap_pair[0], gap_pair[1])

# Example usage
if __name__ == "__main__":
    L, R = 10, 50
    result = largest_prime_gap(L, R)
    if result:
        gap, p1, p2 = result
        print(f"Primes in [{L}, {R}]: {segmented_sieve_primes(L, R)}")
        print(f"Largest gap: {gap} between {p1} and {p2}")
    else:
        print(f"Fewer than 2 primes in [{L}, {R}]")