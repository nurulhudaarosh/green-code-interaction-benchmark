import math
import unittest

def analyze_prime_range(L: int, R: int, include_summary: bool = False) -> dict:
    """
    Analyzes primes in range [L, R] using a segmented sieve.
    
    Args:
        L (int): Lower bound (L >= 1)
        R (int): Upper bound (R >= L)
        include_summary (bool): If True, attaches operation_summary to output.

    Returns:
        dict: Standard result containing 'primes', 'max_gap', 'max_gap_pair',
              and optionally 'operation_summary'.
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

    # Step 2: Segmented Sieve for [L, R]
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

    # Step 3: Find maximum gap with deterministic tie-breaking (first pair wins)
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

    if include_summary:
        result["operation_summary"] = {
            "base_primes_count": len(base_primes),
            "segment_size": segment_size,
            "segment_sieve_steps": sieve_steps,
            "prime_gap_checks": gap_checks
        }

    return result


# --- Unit Tests ---

class TestPrimeRangeAnalyzer(unittest.TestCase):

    def test_smallest_input(self):
        """L=1, R=1: Smallest permitted range input."""
        res = analyze_prime_range(1, 1)
        self.assertEqual(res["primes"], [])
        self.assertEqual(res["max_gap"], 0)
        self.assertIsNone(res["max_gap_pair"])

    def test_single_prime_range(self):
        """Single prime in range (L=2, R=2)."""
        res = analyze_prime_range(2, 2)
        self.assertEqual(res["primes"], [2])
        self.assertEqual(res["max_gap"], 0)
        self.assertIsNone(res["max_gap_pair"])

    def test_no_primes_in_range(self):"""Range with composites only (L=24, R=28)."""
        res = analyze_prime_range(24, 28)
        self.assertEqual(res["primes"], [])
        self.assertEqual(res["max_gap"], 0)
        self.assertIsNone(res["max_gap_pair"])

    def test_inverted_range(self):
        """L > R condition."""
        res = analyze_prime_range(10, 5)
        self.assertEqual(res["primes"], [])
        self.assertEqual(res["max_gap"], 0)
        self.assertIsNone(res["max_gap_pair"])

    def test_deterministic_tie_breaking(self):
        """Verify first pair is selected when maximum gap ties occur."""
        # Range [10, 25]: Primes are [11, 13, 17, 19, 23]
        # Gaps: (13,17)->4, (19,23)->4. First pair (13, 17) must be selected.
        res = analyze_prime_range(10, 25)
        self.assertEqual(res["primes"], [11, 13, 17, 19, 23])
        self.assertEqual(res["max_gap"], 4)
        self.assertEqual(res["max_gap_pair"], (13, 17))

    def test_operation_summary_flag(self):
        """Verify summary inclusion toggling."""
        without_summary = analyze_prime_range(10, 20, include_summary=False)
        self.assertNotIn("operation_summary", without_summary)

        with_summary = analyze_prime_range(10, 20, include_summary=True)
        self.assertIn("operation_summary", with_summary)
        summary = with_summary["operation_summary"]
        self.assertIn("base_primes_count", summary)
        self.assertIn("segment_size", summary)
        self.assertIn("segment_sieve_steps", summary)
        self.assertIn("prime_gap_checks", summary)


if __name__ == "__main__":
    unittest.main()