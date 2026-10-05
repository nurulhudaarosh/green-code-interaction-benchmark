import math

def analyze_prime_range(L: int, R: int):
    """
    Analyzes primes in range [L, R] using segmented sieve.
    
    Returns:
        dict: {
            "primes": list of primes in [L, R],
            "max_gap": largest gap between consecutive primes (0 if < 2 primes),
            "max_gap_pair": tuple (p1, p2) of the FIRST prime pair achieving max_gap (None if < 2 primes)
        }
    """
    if R < 2 or L > R:
        return {"primes": [], "max_gap": 0, "max_gap_pair": None}

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

    for p in base_primes:
        start = max(p * p, ((L + p - 1) // p) * p)
        for multiple in range(start, R + 1, p):
            is_prime_segment[multiple - L] = False

    primes = [L + i for i, is_p in enumerate(is_prime_segment) if is_p]

    # Step 3: Find maximum gap with deterministic tie-handling (first occurring pair wins)
    max_gap = 0
    max_gap_pair = None

    for i in range(len(primes) - 1):
        p1, p2 = primes[i], primes[i + 1]
        gap = p2 - p1
        # Strict inequality ensures deterministic preference for the first pair on ties
        if gap > max_gap:
            max_gap = gap
            max_gap_pair = (p1, p2)

    return {
        "primes": primes,
        "max_gap": max_gap,
        "max_gap_pair": max_gap_pair
    }

# Example demonstrating deterministic tie handling:
if __name__ == "__main__":
    result = analyze_prime_range(10, 25)
    print("Primes:", result["primes"])            # [11, 13, 17, 19, 23]
    print("Max Gap:", result["max_gap"])          # 4
    print("Max Gap Pair:", result["max_gap_pair"]) # (13, 17) - deterministic tie pick