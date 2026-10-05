import unittest
from itertools import combinations
from typing import List, Optional


def min_subset_sum_indices(a: List[int], target: int) -> Optional[List[int]]:
    """
    Return the ascending 0-based index list of a subset of `a` summing to
    `target` with the fewest elements and, among ties, the lexicographically
    smallest index list. Return None if impossible, [] if target == 0.
    Raises ValueError if any element is not a positive integer.
    """
    for v in a:
        if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
            raise ValueError("all elements must be positive integers")

    if target < 0:
        return None
    if target == 0:
        return []          # covers empty input and non-empty input alike

    n = len(a)
    if n == 0:
        return None        # positive target, nothing to choose from

    INF = float("inf")

    # best[i][s] = min count using elements a[i:] summing exactly to s
    best = [[INF] * (target + 1) for _ in range(n + 1)]
    best[n][0] = 0
    for i in range(n - 1, -1, -1):
        v = a[i]
        cur, nxt = best[i], best[i + 1]
        for s in range(target + 1):
            val = nxt[s]
            if v <= s and nxt[s - v] + 1 < val:
                val = nxt[s - v] + 1
            cur[s] = val

    if best[0][target] == INF:
        return None

    # Reconstruct: smallest feasible index at each step => lexicographic min
    result: List[int] = []
    i, s, k = 0, target, best[0][target]
    while k > 0:
        for j in range(i, n):
            v = a[j]
            if v <= s and best[j + 1][s - v] == k - 1:
                result.append(j)
                i, s, k = j + 1, s - v, k - 1
                break
        else:  # unreachable if the DP is correct
            raise RuntimeError("reconstruction failed")
    return result


def _brute_force(a: List[int], target: int) -> Optional[List[int]]:
    """Reference oracle: sizes ascending, combinations in lexicographic order,
    so the first match is the required answer."""
    for size in range(len(a) + 1):
        for idx in combinations(range(len(a)), size):
            if sum(a[i] for i in idx) == target:
                return list(idx)
    return None


class TestMinSubsetSum(unittest.TestCase):
    # --- smallest permitted / empty structures ---
    def test_empty_input_zero_target(self):
        self.assertEqual(min_subset_sum_indices([], 0), [])

    def test_empty_input_positive_target(self):
        self.assertIsNone(min_subset_sum_indices([], 5))

    def test_zero_target_nonempty(self):
        self.assertEqual(min_subset_sum_indices([1, 1, 1, 1], 0), [])

    def test_single_element_match(self):
        self.assertEqual(min_subset_sum_indices([7], 7), [0])

    def test_single_element_mismatch(self):
        self.assertIsNone(min_subset_sum_indices([7], 3))
        self.assertIsNone(min_subset_sum_indices([7], 9))

    # --- unreachable / degenerate targets ---
    def test_all_elements_exceed_target(self):
        self.assertIsNone(min_subset_sum_indices([10, 20, 30], 5))

    def test_parity_unreachable(self):
        self.assertIsNone(min_subset_sum_indices([2, 4, 6], 5))

    def test_target_exceeds_total(self):
        self.assertIsNone(min_subset_sum_indices([1, 2, 3], 7))

    def test_target_equals_total(self):
        self.assertEqual(min_subset_sum_indices([1, 2, 3], 6), [0, 1, 2])

    def test_negative_target(self):
        self.assertIsNone(min_subset_sum_indices([1, 2], -1))

    # --- preserved tie-breaking rules ---
    def test_fewest_elements_beats_lex_order(self):
        # [0,1,2] (1+2+3) is lex-smaller but has 3 elements; [2,3] has 2.
        self.assertEqual(min_subset_sum_indices([1, 2, 3, 3], 6), [2, 3])

    def test_lex_smallest_among_equal_size(self):
        # {4,5}=[1,2] and {2,7}=[3,4] both have size 2; [1,2] is smaller.
        self.assertEqual(min_subset_sum_indices([3, 4, 5, 2, 7], 9), [1, 2])
        self.assertEqual(min_subset_sum_indices([1, 3, 2, 2], 4), [0, 1])

    def test_duplicates_use_smallest_indices(self):
        self.assertEqual(min_subset_sum_indices([5, 5, 5], 10), [0, 1])
        self.assertEqual(min_subset_sum_indices([2, 2, 2, 2], 4), [0, 1])

    def test_output_is_ascending(self):
        r = min_subset_sum_indices([9, 1, 8, 2, 7, 3], 10)
        self.assertEqual(r, sorted(r))

    # --- invalid input ---
    def test_invalid_elements_raise(self):
        for bad in ([0], [-1, 2], [1.5], ["3"], [True]):
            with self.assertRaises(ValueError):
                min_subset_sum_indices(bad, 1)

    # --- exhaustive cross-check against the oracle ---
    def test_matches_brute_force(self):
        # Deterministic enumeration of all arrays over values 1..4, length 0..5.
        from itertools import product
        for n in range(0, 6):
            for arr in product(range(1, 5), repeat=n):
                arr = list(arr)
                for t in range(0, sum(arr) + 3):
                    self.assertEqual(
                        min_subset_sum_indices(arr, t),
                        _brute_force(arr, t),
                        msg=f"a={arr}, T={t}",
                    )


if __name__ == "__main__":
    unittest.main()