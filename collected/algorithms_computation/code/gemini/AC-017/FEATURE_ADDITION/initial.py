import math

def max_prime_gap_in_range(L: int, R: int):
    """
    Finds all primes in [L, R] using a Segmented Sieve and returns
    a tuple: (list_of_primes, largest_gap)
    """
    if R < 2 or L > R:
        return ([], 0)

    # Step 1: Find base primes up to sqrt(R)
    limit = math.isqrt(R)
    base_is_prime = [True] * (limit + 1)
    if limit >= 0:
        base_is_prime[0] = False
    if limit >= 1:
        base_is_prime[1] = False

    for i in range(2, math.isqrt(limit) + 1):
        if base_is_prime[i]:
            for j in range(i * i, limit + 1, i):
                base_is_prime[j] = False

    base_primes = [i for i in range(2, limit + 1) if base_is_prime[i]]

    # Step 2: Segmented Sieve for [L, R]
    segment_size = R - L + 1
    segment_is_prime = [True] * segment_size

    # Mark numbers < 2 as non-prime
    for num in range(L, min(R + 1, 2)):
        segment_is_prime[num - L] = False

    # Mark multiples of base primes in [L, R]
    for p in base_primes:
        # Find the smallest multiple of p >= L
        start = max(p * p, ((L + p - 1) // p) * p)
        for j in range(start, R + 1, p):
            segment_is_prime[j - L] = False

    # Step 3: Collect primes in [L, R]
    primes = [L + i for i in range(segment_size) if segment_is_prime[i]]

    # Step 4: Calculate maximum gap
    max_gap = 0
    if len(primes) >= 2:
        max_gap = max(primes[i] - primes[i - 1] for i in range(1, len(primes)))

    return primes, max_gap


# --- Example Usage ---
if __name__ == "__main__":
    L_val, R_val = 1, 100
    primes, largest_gap = max_prime_gap_in_range(L_val, R_val)
    
    print(f"Primes in [{L_val}, {R_val}]: {primes}")
    print(f"Largest Gap: {largest_gap}")