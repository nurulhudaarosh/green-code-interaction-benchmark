import math

def analyze_prime_range(L: int, R: int, include_summary: bool = False):
    """
    Analyzes primes in range [L, R] using segmented sieve.
    
    Args:
        L (int): Lower bound (L >= 1)
        R (int): Upper bound (R >= L)
        include_summary (bool): If True, attaches operation_summary to output.

    Returns:
        dict: Standard result with optional 'operation_summary' field.
    """
    if R < 2 or L > R:
        result = {
            "primes": [],
            "max_gap": 0,
            "max_gap_pair": None
        }
        if include_summary:
            result["operation_summary"] = {
                "base_primes_count": 0,
                "segment_size": max(0, R - L + 1),
                "segment_sieve_steps": 0,
                "prime_gap_checks": 0
            }
        return result

    # Step 1: Base prime generation up to floor(sqrt(R))
    limit = math.isqrt(R)
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, math.isqrt(limit) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False

    base_primes = [i for i, is_p in enumerate(sieve) if is_p]

    # Step 2: Segmented Sieve
    segment_size = R - L + 1
    is_prime_segment = [True] * segment_size

    if L == 1:
        is_prime_segment[0] = False

    sieve_steps = 0
    for p in base_primes:
        start = max(p * p, ((L + p - 1) // p) * p)
        for multiple in range(start, R + 1, p):
            is_prime_segment[multiple - L] = False
            sieve_steps += 1

    primes = [L + i for i, is_p in enumerate(is_prime_segment) if is_p]

    # Step 3: Find maximum gap with deterministic tie-handling (first occurring pair wins)
    max_gap = 0
    max_gap_pair = None
    gap_checks = max(0, len(primes) - 1)

    for i in range(len(primes) - 1):
        p1, p2 = primes[i], primes[i + 1]
        gap = p2 - p1
        if gap > max_gap:
            max_gap = gap
            max_gap_pair = (p1, p2)

    result = {
        "primes": primes,
        "max_gap": max_gap,
        "max_gap_pair": max_gap_pair
    }

    # Attach operational summary only when explicitly requested
    if include_summary:
        result["operation_summary"] = {
            "base_primes_count": len(base_primes),
            "segment_size": segment_size,
            "segment_sieve_steps": sieve_steps,
            "prime_gap_checks": gap_checks
        }

    return result


# Example Usage
if __name__ == "__main__":
    # 1. Feature disabled (default behavior preserved)
    standard_res = analyze_prime_range(10, 25)
    print("Standard Output:", standard_res)

    # 2. Feature enabled
    summary_res = analyze_prime_range(10, 25, include_summary=True)
    print("\nWith Operational Summary:", summary_res)