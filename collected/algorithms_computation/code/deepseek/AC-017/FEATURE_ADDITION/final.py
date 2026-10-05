import math

def simple_sieve(limit):
    """Return (primes, mark_operations) up to limit using Sieve of Eratosthenes."""
    if limit < 2:
        return [], 0
    sieve = bytearray(b'\x01') * (limit + 1)
    sieve[0:2] = b'\x00\x00'
    mark_operations = 0
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            start = i * i
            sieve[start:limit + 1:i] = b'\x00' * (((limit - start) // i) + 1)
            mark_operations += 1
    primes = [i for i in range(2, limit + 1) if sieve[i]]
    return primes, mark_operations


def largest_prime_gap(L, R, include_operation_summary=False):
    """
    Return the largest gap between consecutive primes in [L, R].

    Returns:
        dict with keys:
            - 'largest_gap'      : int or None
            - 'operation_summary': dict (only if include_operation_summary=True)

    If fewer than 2 primes exist in the interval, 'largest_gap' is None.
    """
    result = {"largest_gap": None}

    if R < 2:
        if include_operation_summary:
            result["operation_summary"] = {
                "base_sieve_marks": 0,
                "segment_marks": 0,
                "prime_scans": 0,
                "gap_comparisons": 0,
                "total": 0,
            }
        return result

    L = max(L, 2)

    # Base primes up to sqrt(R)
    limit = math.isqrt(R)
    base_primes, base_sieve_marks = simple_sieve(limit)

    # Segmented sieve over [L, R]
    size = R - L + 1
    is_prime = bytearray(b'\x01') * size

    segment_marks = 0
    for p in base_primes:
        start = max(p * p, ((L + p - 1) // p) * p)
        if start <= R:
            segment_marks += 1
            for multiple in range(start, R + 1, p):
                is_prime[multiple - L] = 0

    # Collect primes in [L, R]
    primes = []
    prime_scans = 0
    for i in range(size):
        prime_scans += 1
        if is_prime[i]:
            primes.append(L + i)

    if len(primes) < 2:
        if include_operation_summary:
            result["operation_summary"] = {
                "base_sieve_marks": base_sieve_marks,
                "segment_marks": segment_marks,
                "prime_scans": prime_scans,
                "gap_comparisons": 0,
                "total": base_sieve_marks + segment_marks + prime_scans,
            }
        return result

    # Find maximum gap
    max_gap = 0
    gap_comparisons = 0
    for i in range(1, len(primes)):
        gap_comparisons += 1
        gap = primes[i] - primes[i - 1]
        if gap > max_gap:
            max_gap = gap

    result["largest_gap"] = max_gap

    if include_operation_summary:
        total = base_sieve_marks + segment_marks + prime_scans + gap_comparisons
        result["operation_summary"] = {
            "base_sieve_marks": base_sieve_marks,
            "segment_marks": segment_marks,
            "prime_scans": prime_scans,
            "gap_comparisons": gap_comparisons,
            "total": total,
        }

    return result


if __name__ == "__main__":
    # Original behavior (feature disabled / not requested)
    print(largest_prime_gap(10, 50))
    # -> {'largest_gap': 6}

    # With the new feature enabled
    print(largest_prime_gap(10, 50, include_operation_summary=True))
    # -> {'largest_gap': 6, 'operation_summary': {...}}