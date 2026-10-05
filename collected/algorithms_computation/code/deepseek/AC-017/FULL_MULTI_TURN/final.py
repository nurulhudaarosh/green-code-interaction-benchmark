import math
import unittest
from typing import List, Tuple, Optional, Dict, Any

# ---------------------------------------------------------------------------
# Implementation (unchanged original outputs + optional operation_summary)
# ---------------------------------------------------------------------------

def sieve_primes(limit: int) -> Tuple[List[int], int]:
    """Generate all primes up to limit using the Sieve of Eratosthenes.
    Returns (primes, base_sieve_decisions)."""
    if limit < 2:
        return [], 0
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    decisions = 0
    root = int(math.sqrt(limit))
    for i in range(2, root + 1):
        decisions += 1
        if is_prime[i]:
            if i * i <= limit:
                decisions += 1
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
    return [i for i in range(2, limit + 1) if is_prime[i]], decisions

def segmented_sieve(L: int, R: int, include_summary: bool = False) -> Dict[str, Any]:
    """Primes in [L, R], largest gap, deterministic leftmost gap pair.
    Optionally adds 'operation_summary' (deterministic decision counts)."""
    result: Dict[str, Any] = {"primes": [], "largest_gap": None, "gap_pair": None}

    if L > R:
        if include_summary:
            result["operation_summary"] = _empty_summary()
        return result

    L = max(L, 2)  # no primes below 2
    if L > R:
        if include_summary:
            result["operation_summary"] = _empty_summary()
        return result

    limit = int(math.sqrt(R)) + 1
    base_primes, base_sieve_decisions = sieve_primes(limit)

    base_marking_decisions = 0
    for p in base_primes:
        if p * p <= limit:
            base_marking_decisions += 1

    segment_size = R - L + 1
    is_prime = [True] * segment_size

    segment_marking_decisions = 0
    for p in base_primes:
        segment_marking_decisions += 1
        start = max(p * p, ((L + p - 1) // p) * p)
        for multiple in range(start, R + 1, p):
            is_prime[multiple - L] = False

    segment_scan_decisions = segment_size
    primes = [L + i for i in range(segment_size) if is_prime[i]]
    result["primes"] = primes

    if len(primes) < 2:
        if include_summary:
            result["operation_summary"] = _build_summary(
                base_sieve_decisions, base_marking_decisions,
                segment_marking_decisions, segment_scan_decisions, 0)
        return result

    largest_gap = -1
    gap_pair: Optional[Tuple[int, int]] = None
    gap_comparison_decisions = 0
    for i in range(len(primes) - 1):
        gap_comparison_decisions += 1
        gap = primes[i + 1] - primes[i]
        if gap > largest_gap:  # strict '>' => leftmost wins on ties
            largest_gap = gap
            gap_pair = (primes[i], primes[i + 1])

    result["largest_gap"] = largest_gap
    result["gap_pair"] = gap_pair

    if include_summary:
        result["operation_summary"] = _build_summary(
            base_sieve_decisions, base_marking_decisions,
            segment_marking_decisions, segment_scan_decisions,
            gap_comparison_decisions)
    return result

def _build_summary(bsd, bmd, smd, ssd, gcd) -> Dict[str, int]:
    return {
        "base_sieve_decisions": bsd,
        "base_marking_decisions": bmd,
        "segment_marking_decisions": smd,
        "segment_scan_decisions": ssd,
        "gap_comparison_decisions": gcd,
        "total_decisions": bsd + bmd + smd + ssd + gcd,
    }

def _empty_summary() -> Dict[str, int]:
    return {
        "base_sieve_decisions": 0, "base_marking_decisions": 0,
        "segment_marking_decisions": 0, "segment_scan_decisions": 0,
        "gap_comparison_decisions": 0, "total_decisions": 0,
    }

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPrimeRangeAnalyzer(unittest.TestCase):

    # ----- Original behavior (regression) -----
    def test_basic_range(self):
        r = segmented_sieve(10, 30)
        self.assertEqual(r["primes"], [11, 13, 17, 19, 23, 29])
        self.assertEqual(r["largest_gap"], 6)
        self.assertEqual(r["gap_pair"], (23, 29))

    def test_deterministic_tie_breaking_leftmost(self):
        # Max gap 4 occurs at (7,11) and (13,17); leftmost must win.
        r = segmented_sieve(3, 19)
        self.assertEqual(r["primes"], [3, 5, 7, 11, 13, 17, 19])
        self.assertEqual(r["largest_gap"], 4)
        self.assertEqual(r["gap_pair"], (7, 11))

    def test_two_primes_gap_one(self):
        r = segmented_sieve(2, 3)
        self.assertEqual(r["primes"], [2, 3])
        self.assertEqual(r["largest_gap"], 1)
        self.assertEqual(r["gap_pair"], (2, 3))

    # ----- Difficult case 1: smallest permitted input -----
    def test_smallest_permitted_input(self):
        r = segmented_sieve(2, 2)
        self.assertEqual(r["primes"], [2])
        self.assertIsNone(r["largest_gap"])
        self.assertIsNone(r["gap_pair"])

    def test_smallest_permitted_input_with_summary(self):
        r = segmented_sieve(2, 2, include_summary=True)
        self.assertEqual(r["primes"], [2])
        self.assertIsNone(r["largest_gap"])
        self.assertIsNone(r["gap_pair"])
        self.assertIn("operation_summary", r)
        self.assertEqual(r["operation_summary"]["gap_comparison_decisions"], 0)
        self.assertGreater(r["operation_summary"]["total_decisions"], 0)

    def test_input_just_below_two_touching_two(self):
        r = segmented_sieve(1, 2)
        self.assertEqual(r["primes"], [2])
        self.assertIsNone(r["largest_gap"])
        self.assertIsNone(r["gap_pair"])

    # ----- Difficult case 2: empty structures where allowed -----
    def test_empty_interval_L_greater_than_R(self):
        r = segmented_sieve(10, 9)
        self.assertEqual(r["primes"], [])
        self.assertIsNone(r["largest_gap"])
        self.assertIsNone(r["gap_pair"])

    def test_empty_interval_with_summary(self):
        r = segmented_sieve(10, 9, include_summary=True)
        self.assertEqual(r["primes"], [])
        self.assertIsNone(r["largest_gap"])
        self.assertIsNone(r["gap_pair"])
        self.assertEqual(r["operation_summary"]["total_decisions"], 0)

    def test_no_primes_in_valid_range(self):
        for L, R in [(24, 28), (14, 16), (90, 96), (114, 126)]:
            r = segmented_sieve(L, R)
            self.assertEqual(r["primes"], [], f"range [{L},{R}]")
            self.assertIsNone(r["largest_gap"])
            self.assertIsNone(r["gap_pair"])

    def test_single_point_composite(self):
        for x in [0, 1, 4, 9, 15, 100]:
            r = segmented_sieve(x, x)
            self.assertEqual(r["primes"], [], f"x={x}")
            self.assertIsNone(r["largest_gap"])
            self.assertIsNone(r["gap_pair"])

    def test_range_fully_below_two(self):
        r = segmented_sieve(-10, 1)
        self.assertEqual(r["primes"], [])
        self.assertIsNone(r["largest_gap"])
        self.assertIsNone(r["gap_pair"])

    def test_negative_to_small_prime(self):
        r = segmented_sieve(-5, 5)
        self.assertEqual(r["primes"], [2, 3, 5])
        self.assertEqual(r["largest_gap"], 1)
        self.assertEqual(r["gap_pair"], (2, 3))  # leftmost on tie with (3,5)

    # ----- Determinism: repeated calls give identical results -----
    def test_determinism_repeated_calls(self):
        for L, R in [(3, 19), (10, 30), (2, 2), (10, 9), (24, 28)]:
            a = segmented_sieve(L, R)
            b = segmented_sieve(L, R)
            self.assertEqual(a, b)

    # ----- Backward compatibility: no summary unless requested -----
    def test_no_summary_by_default(self):
        r = segmented_sieve(10, 30)
        self.assertNotIn("operation_summary", r)
        self.assertEqual(set(r.keys()), {"primes", "largest_gap", "gap_pair"})

    # ----- Feature enabled does not disturb original fields -----
    def test_summary_does_not_change_original_fields(self):
        plain = segmented_sieve(3, 19)
        with_sum = segmented_sieve(3, 19, include_summary=True)
        self.assertEqual(plain["primes"], with_sum["primes"])
        self.assertEqual(plain["largest_gap"], with_sum["largest_gap"])
        self.assertEqual(plain["gap_pair"], with_sum["gap_pair"])
        self.assertEqual(with_sum["gap_pair"], (7, 11))

if __name__ == "__main__":
    unittest.main(verbosity=2)