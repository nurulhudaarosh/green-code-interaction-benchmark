import math

def max_prime_gap(L: int, R: int):
    """
    Finds all prime numbers in the range [L, R] and returns:
    - primes: List of all prime numbers in [L, R]
    - max_gap: The largest gap between consecutive primes in [L, R] (0 if < 2 primes)
    """
    if R < 2 or L > R:
        return [], 0
    
    # Step 1: Find base primes up to floor(sqrt(R))
    limit = math.isqrt(R)
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, math.isqrt(limit) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    
    base_primes = [i for i, is_p in enumerate(sieve) if is_p]

    # Step 2: Segmented sieve for [L, R]
    segment_size = R - L + 1
    is_prime_segment = [True] * segment_size

    # Handle edge case where L = 1
    if L == 1:
        is_prime_segment[0] = False

    for p in base_primes:
        # Find the smallest multiple of p >= L, starting at least from p^2
        start = max(p * p, ((L + p - 1) // p) * p)
        
        for multiple in range(start, R + 1, p):
            is_prime_segment[multiple - L] = False

    # Collect primes in [L, R]
    primes = [L + i for i, is_p in enumerate(is_prime_segment) if is_p]

    # Step 3: Find the maximum gap between consecutive primes
    max_gap = 0
    for i in range(len(primes) - 1):
        gap = primes[i + 1] - primes[i]
        if gap > max_gap:
            max_gap = gap

    return primes, max_gap

# Example Usage:
if __name__ == "__main__":
    L, R = 100, 200
    primes, gap = max_prime_gap(L, R)
    print(f"Primes in [{L}, {R}]: {primes}")
    print(f"Maximum gap: {gap}")