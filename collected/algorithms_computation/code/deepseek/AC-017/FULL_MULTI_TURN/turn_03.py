import math
from typing import List, Tuple, Optional, Dict, Any

def sieve_primes(limit: int) -> Tuple[List[int], int]:
    """
    Generate all primes up to limit using the Sieve of Eratosthenes.
    Returns (primes, decisions) where decisions counts major operations:
      - one decision per candidate i in [2, sqrt(limit)]
      - one decision per prime p whose inner marking loop is entered
    """
    if limit < 2:
        return [], 0

    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False

    decisions = 0
    root = int(math.sqrt(limit))
    for i in range(2, root + 1):
        decisions += 1  # base-prime sieve decision on is_prime[i]
        if is_prime[i]:
            # entering the marking loop is a decision
            if i * i <= limit:
                decisions += 1
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False

    return [i for i in range(2, limit + 1) if is_prime[i]], decisions

def segmented_sieve(
    L: int,
    R: int,
    include_summary: bool = False,
) -> Dict[str, Any]:
    """
    Find all primes in [L, R] using a segmented sieve.

    Always returns a dict with the ORIGINAL required fields:
      - 'primes':        sorted list of primes in [L, R]
      - 'largest_gap':   max consecutive gap, or None if < 2 primes
      - 'gap_pair':      deterministic leftmost (a, b) achieving largest_gap,
                         or None if < 2 primes

    If include_summary=True, adds:
      - 'operation_summary': {
            'base_sieve_decisions': int,
            'base_marking_decisions': int,
            'segment_marking_decisions': int,
            'segment_scan_decisions': int,
            'gap_comparison_decisions': int,
            'total_decisions': int,
        }
    """
    result: Dict[str, Any] = {
        "primes": [],
        "largest_gap": None,
        "gap_pair": None,
    }

    if L > R:
        if include_summary:
            result["operation_summary"] = _empty_summary()
        return result

    L = max(L, 2)  # no primes below 2
    if L > R:
        if include_summary:
            result["operation_summary"] = _empty_summary()
        return result

    # 1) Base primes through sqrt(R)
    limit = int(math.sqrt(R)) + 1
    base_primes, base_sieve_decisions = sieve_primes(limit)

    # Recompute base marking decisions deterministically for the summary,
    # counting exactly one decision per base prime that has a non-empty
    # marking range [p*p, limit]. (sieve_primes already counted these,
    # but we separate them here for a clear summary breakdown.)
    base_marking_decisions = 0
    for p in base_primes:
        if p * p <= limit:
            base_marking_decisions += 1

    # 2) Segmented sieve over [L, R]
    segment_size = R - L + 1
    is_prime = [True] * segment_size

    segment_marking_decisions = 0
    for p in base_primes:
        segment_marking_decisions += 1  # decision to mark for this prime
        start = max(p * p, ((L + p - 1) // p) * p)
        for multiple in range(start, R + 1, p):
            is_prime[multiple - L] = False

    # 3) Segment scan
    segment_scan_decisions = segment_size
    primes = [L + i for i in range(segment_size) if is_prime[i]]

    result["primes"] = primes

    # 4) Deterministic largest gap: leftmost pair wins on ties (strict '>')
    if len(primes) < 2:
        if include_summary:
            result["operation_summary"] = _build_summary(
                base_sieve_decisions,
                base_marking_decisions,
                segment_marking_decisions,
                segment_scan_decisions,
                0,
            )
        return result

    largest_gap = -1
    gap_pair: Optional[Tuple[int, int]] = None
    gap_comparison_decisions = 0
    for i in range(len(primes) - 1):
        gap_comparison_decisions += 1
        gap = primes[i + 1] - primes[i]
        if gap > largest_gap:  # strict '>' => keep leftmost on ties
            largest_gap = gap
            gap_pair = (primes[i], primes[i + 1])

    result["largest_gap"] = largest_gap
    result["gap_pair"] = gap_pair

    if include_summary:
        result["operation_summary"] = _build_summary(
            base_sieve_decisions,
            base_marking_decisions,
            segment_marking_decisions,
            segment_scan_decisions,
            gap_comparison_decisions,
        )

    return result

def _build_summary(
    base_sieve_decisions: int,
    base_marking_decisions: int,
    segment_marking_decisions: int,
    segment_scan_decisions: int,
    gap_comparison_decisions: int,
) -> Dict[str, int]:
    return {
        "base_sieve_decisions": base_sieve_decisions,
        "base_marking_decisions": base_marking_decisions,
        "segment_marking_decisions": segment_marking_decisions,
        "segment_scan_decisions": segment_scan_decisions,
        "gap_comparison_decisions": gap_comparison_decisions,
        "total_decisions": (
            base_sieve_decisions
            + base_marking_decisions
            + segment_marking_decisions
            + segment_scan_decisions
            + gap_comparison_decisions
        ),
    }

def _empty_summary() -> Dict[str, int]:
    return {
        "base_sieve_decisions": 0,
        "base_marking_decisions": 0,
        "segment_marking_decisions": 0,
        "segment_scan_decisions": 0,
        "gap_comparison_decisions": 0,
        "total_decisions": 0,
    }

def solve(L: int, R: int, include_summary: bool = False) -> None:
    """Print the required outputs for [L, R]; optionally include the operation summary."""
    res = segmented_sieve(L, R, include_summary=include_summary)
    primes = res["primes"]
    largest_gap = res["largest_gap"]
    gap_pair = res["gap_pair"]

    if not primes:
        print(f"No primes in [{L}, {R}]")
    elif largest_gap is None:
        print(f"Only one prime in [{L}, {R}]: {primes[0]}")
    else:
        print(f"Primes in [{L}, {R}]: {primes}")
        print(f"Largest gap: {largest_gap} between {gap_pair[0]} and {gap_pair[1]}")

    if include_summary:
        print(f"Operation summary: {res['operation_summary']}")

if __name__ == "__main__":
    # Tie case [3, 19]: max gap 4 at (7,11) and (13,17) -> leftmost (7,11).
    print("=== Feature disabled (original behavior, unchanged) ===")
    for L, R in [(3, 19), (10, 30), (1, 10), (14, 16), (2, 3), (100, 200)]:
        print(f"\n--- Interval [{L}, {R}] ---")
        solve(L, R)

    print("\n=== Feature enabled (operation_summary added) ===")
    for L, R in [(3, 19), (10, 30)]:
        print(f"\n--- Interval [{L}, {R}] ---")
        solve(L, R, include_summary=True)