from math import isqrt

def analyze_primes(lo, hi, include_operation_summary=False):
    if not isinstance(lo, int) or not isinstance(hi, int) or lo > hi:
        raise ValueError("lo and hi must be integers with lo <= hi")

    markings = 0
    base_scanned = 0
    candidates = hi - lo + 1

    primes = []
    if hi >= 2:
        # Sieve of Eratosthenes up to hi
        is_prime = [True] * (hi + 1)
        is_prime[0] = False
        if hi >= 1:
            is_prime[1] = False
        for p in range(2, isqrt(hi) + 1):
            if is_prime[p]:
                base_scanned += 1
                for m in range(p * p, hi + 1, p):
                    if is_prime[m]:
                        pass
                    is_prime[m] = False
                    markings += 1
        primes = [n for n in range(max(lo, 2), hi + 1) if is_prime[n]]

    gap_comparisons = max(len(primes) - 1, 0)
    largest_gap = max(
        (b - a for a, b in zip(primes, primes[1:])), default=0
    )

    result = {
        "primes": primes,
        "count": len(primes),
        "sum": sum(primes),
        "min": primes[0] if primes else None,
        "max": primes[-1] if primes else None,
        "largest_gap": largest_gap,
    }

    if include_operation_summary:
        result["operation_summary"] = {
            "candidates_examined": candidates,
            "sieve_markings": markings,
            "sieve_primes_scanned": base_scanned,
            "gap_comparisons": gap_comparisons,
            "total_operations": candidates + markings + base_scanned + gap_comparisons,
        }
    return result