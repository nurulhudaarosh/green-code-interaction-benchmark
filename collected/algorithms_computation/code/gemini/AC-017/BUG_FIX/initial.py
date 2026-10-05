import math

def max_prime_gap(L: int, R: int) -> int:

    if R < 2 or L > R:
        return 0

    # Ensure L is at least 2 for prime checking
    segment_low = max(2, L)
    segment_high = R
    
    if segment_low > segment_high:
        return 0

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

    base_primes = [i for i, is_p in enumerate(base_is_prime) if is_p]

    # Step 2: Segmented Sieve on [segment_low, segment_high]
    range_len = segment_high - segment_low + 1
    is_prime_in_range = [True] * range_len

    for p in base_primes:
        # Find the smallest multiple of p >= segment_low
        start_multiple = max(p * p, ((segment_low + p - 1) // p) * p)
        
        for multiple in range(start_multiple, segment_high + 1, p):
            is_prime_in_range[multiple - segment_low] = False

    # Collect primes in range [L, R]
    primes = [
        segment_low + i
        for i, is_p in enumerate(is_prime_in_range)
        if is_p
    ]

    # Step 3: Compute maximum consecutive prime gap
    if len(primes) < 2:
        return 0

    max_gap = max(primes[i] - primes[i - 1] for i in range(1, len(primes)))
    return max_gap


# Example usage
if __name__ == "__main__":
    L_val, R_val = 1000000000, 1001000000
    print(f"Max prime gap in [{L_val}, {R_val}]: {max_prime_gap(L_val, R_val)}")