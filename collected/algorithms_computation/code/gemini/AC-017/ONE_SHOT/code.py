import math

def max_prime_gap(L: int, R: int) -> int:
    """
    Finds the maximum gap between consecutive primes in the closed interval [L, R].
    Uses Segmented Sieve of Eratosthenes.
    """
    if R < 2 or L >= R:
        return 0

    limit = math.isqrt(R)
    
    # Step 1: Base sieve up to sqrt(R)
    base_is_prime = [True] * (limit + 1)
    base_is_prime[0] = base_is_prime[1] = False
    for i in range(2, math.isqrt(limit) + 1):
        if base_is_prime[i]:
            for j in range(i * i, limit + 1, i):
                base_is_prime[j] = False
                
    base_primes = [p for p in range(2, limit + 1) if base_is_prime[p]]

    # Step 2: Segmented sieve on [L, R]
    segment_size = R - L + 1
    is_prime = [True] * segment_size

    for p in base_primes:
        # Find smallest multiple of p >= L and >= p * p
        start = max(p * p, ((L + p - 1) // p) * p)
        for j in range(start, R + 1, p):
            is_prime[j - L] = False

    # 1 is not a prime number
    if L == 1:
        is_prime[0] = False

    # Step 3: Collect primes and calculate the largest gap
    primes_in_range = [L + i for i in range(segment_size) if is_prime[i]]

    if len(primes_in_range) < 2:
        return 0

    max_gap = 0
    for i in range(len(primes_in_range) - 1):
        gap = primes_in_range[i + 1] - primes_in_range[i]
        if gap > max_gap:
            max_gap = gap

    return max_gap


# Example Usage:
if __name__ == "__main__":
    L, R = 1, 100
    print(f"Max prime gap in [{L}, {R}]:", max_prime_gap(L, R))  # Output: 8 (between 89 and 97)