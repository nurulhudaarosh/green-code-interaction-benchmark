from typing import Sequence, List, Dict, Any
import unittest


def longest_increasing_route(a: Sequence[int]) -> Dict[str, Any]:
    """
    Find a longest strictly increasing subsequence.

    Among all longest subsequences, return the one whose sequence
    of original indices is lexicographically smallest.

    Uses O(n^2) dynamic programming with explicit predecessor/index-
    sequence tie breaking.
    """
    n = len(a)

    # Empty input is an allowed disconnected/boundary structure.
    if n == 0:
        return {
            "length": 0,
            "values": [],
            "indices": [],
        }

    # dp_len[i] = maximum length of a strictly increasing subsequence
    # ending at original index i.
    dp_len = [1] * n

    # predecessor[i] = selected predecessor for the optimal subsequence
    # ending at i.
    predecessor = [None] * n

    # index_seq[i] = lexicographically smallest original-index sequence
    # among all optimal subsequences ending at i.
    index_seq: List[List[int]] = [[i] for i in range(n)]

    # O(n^2) dynamic programming.
    for i in range(n):
        for j in range(i):
            # Strictly increasing means equal values cannot be used.
            if a[j] < a[i]:
                candidate_len = dp_len[j] + 1

                if candidate_len > dp_len[i]:
                    dp_len[i] = candidate_len
                    predecessor[i] = j
                    index_seq[i] = index_seq[j] + [i]

                elif candidate_len == dp_len[i]:
                    candidate_indices = index_seq[j] + [i]

                    # Preserve the lexicographically smallest
                    # original-index sequence.
                    if candidate_indices < index_seq[i]:
                        predecessor[i] = j
                        index_seq[i] = candidate_indices

    # Choose the globally optimal endpoint.
    # Primary criterion: maximum length.
    # Secondary criterion: lexicographically smallest index sequence.
    best_i = 0

    for i in range(1, n):
        if dp_len[i] > dp_len[best_i]:
            best_i = i
        elif dp_len[i] == dp_len[best_i]:
            if index_seq[i] < index_seq[best_i]:
                best_i = i

    best_indices = index_seq[best_i]
    best_values = [a[i] for i in best_indices]

    return {
        "length": dp_len[best_i],
        "values": best_values,
        "indices": best_indices,
    }


class TestLongestIncreasingRoute(unittest.TestCase):

    def test_empty_input(self):
        """Empty/disconnected structure should return an empty result."""
        self.assertEqual(
            longest_increasing_route([]),
            {
                "length": 0,
                "values": [],
                "indices": [],
            },
        )

    def test_smallest_non_empty_input(self):
        """A single element is the smallest non-empty input."""
        self.assertEqual(
            longest_increasing_route([42]),
            {
                "length": 1,
                "values": [42],
                "indices": [0],
            },
        )

    def test_single_element_negative(self):
        """Single negative value is still a valid length-one route."""
        self.assertEqual(
            longest_increasing_route([-7]),
            {
                "length": 1,
                "values": [-7],
                "indices": [0],
            },
        )

    def test_all_equal_values(self):
        """
        No two elements can be selected because the subsequence must
        be strictly increasing.
        """
        self.assertEqual(
            longest_increasing_route([5, 5, 5, 5]),
            {
                "length": 1,
                "values": [5],
                "indices": [0],
            },
        )

    def test_strictly_decreasing(self):
        """
        A disconnected structure with no increasing pair.
        The earliest index wins the length-one tie.
        """
        self.assertEqual(
            longest_increasing_route([5, 4, 3, 2, 1]),
            {
                "length": 1,
                "values": [5],
                "indices": [0],
            },
        )

    def test_strictly_increasing(self):
        """Every element belongs to the unique longest route."""
        self.assertEqual(
            longest_increasing_route([1, 2, 3, 4]),
            {
                "length": 4,
                "values": [1, 2, 3, 4],
                "indices": [0, 1, 2, 3],
            },
        )

    def test_lexicographic_index_tie_break(self):
        """
        [1, 3, 4] and [1, 2, 4] both have length three.
        Their index sequences are [0, 1, 3] and [0, 2, 3],
        so [0, 1, 3] is lexicographically smaller.
        """
        self.assertEqual(
            longest_increasing_route([1, 3, 2, 4]),
            {
                "length": 3,
                "values": [1, 3, 4],
                "indices": [0, 1, 3],
            },
        )

    def test_optimal_route_can_start_later(self):
        """The longest route need not start at index zero."""
        self.assertEqual(
            longest_increasing_route([9, 1, 2, 3]),
            {
                "length": 3,
                "values": [1, 2, 3],
                "indices": [1, 2, 3],
            },
        )

    def test_original_example(self):
        self.assertEqual(
            longest_increasing_route([3, 4, 1, 2, 5]),
            {
                "length": 3,
                "values": [3, 4, 5],
                "indices": [0, 1, 4],
            },
        )


if __name__ == "__main__":
    unittest.main()