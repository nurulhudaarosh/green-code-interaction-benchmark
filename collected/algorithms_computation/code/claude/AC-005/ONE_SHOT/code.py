"""
lis_lexsmallest.py

Find a strictly increasing subsequence of maximum length in an integer
sequence, returning the lexicographically smallest sequence of ORIGINAL
INDICES among all subsequences achieving that maximum length.

Algorithm (deterministic, O(n^2) time, O(n) space):
  1. g[i] = length of the longest strictly increasing subsequence that
     STARTS at index i, computed by an O(n^2) DP scanning right-to-left:
         g[i] = 1 + max( g[j] for j > i if a[j] > a[i] ), else 1
  2. L = max(g)  -> the optimal (maximum) subsequence length.
  3. Greedily construct the index sequence left-to-right: at each step,
     among all indices i that (a) come after the last chosen index,
     (b) have a[i] greater than the last chosen value, and (c) have
     g[i] equal to the length still needed, choose the SMALLEST such i.
     This earliest-feasible-choice rule yields the lexicographically
     smallest index sequence, because g[i] certifies that a valid
     completion of the remaining required length exists starting at i.

No external services, network access, randomness, or human interaction
are used; only the Python standard library.
"""

from typing import List, Sequence


def lis_lexsmallest_indices(seq: Sequence[int]) -> List[int]:
    """
    Return the list of original indices of a strictly increasing
    subsequence of maximum length in `seq`. Among all subsequences of
    maximum length, the returned index sequence is the lexicographically
    smallest one.

    Args:
        seq: sequence of integers (list/tuple), possibly empty, possibly
             containing duplicates or negative numbers.

    Returns:
        A list of 0-based indices, strictly increasing, such that
        seq[indices[0]] < seq[indices[1]] < ... , of maximum possible
        length, chosen to be lexicographically smallest among ties.
    """
    n = len(seq)
    if n == 0:
        return []

    # Step 1: g[i] = length of longest strictly increasing subsequence
    # starting at index i. O(n^2) DP, right to left.
    g = [1] * n
    for i in range(n - 1, -1, -1):
        best = 1
        ai = seq[i]
        for j in range(i + 1, n):
            if seq[j] > ai and g[j] + 1 > best:
                best = g[j] + 1
        g[i] = best

    # Step 2: overall optimal length.
    L = max(g)

    # Step 3: greedy left-to-right construction with earliest-feasible choice.
    result: List[int] = []
    last_index = -1
    last_value = None
    remaining = L

    for i in range(n):
        if g[i] != remaining:
            continue
        if i <= last_index:
            continue
        if last_value is not None and not (seq[i] > last_value):
            continue
        result.append(i)
        last_index = i
        last_value = seq[i]
        remaining -= 1
        if remaining == 0:
            break

    return result


def _verify(seq: Sequence[int], indices: List[int]) -> bool:
    """Sanity check: indices strictly increasing and values strictly increasing."""
    for a, b in zip(indices, indices[1:]):
        if not (a < b and seq[a] < seq[b]):
            return False
    return True


def _run_demo() -> None:
    test_cases = [
        [],
        [5],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [2, 2, 2, 2],
        [3, 1, 4, 1, 5, 9, 2, 6],
        [10, 9, 2, 5, 3, 7, 101, 18],
        [0, 1, 0, 3, 2, 3],
        [-1, -2, 0, -3, 4, -5, 5],
        [1, 3, 6, 7, 9, 4, 10, 5, 6],
    ]

    for seq in test_cases:
        indices = lis_lexsmallest_indices(seq)
        values = [seq[i] for i in indices]
        ok = _verify(seq, indices)
        print(f"seq={seq}")
        print(f"  indices={indices} values={values} valid_increasing={ok}")
        print()


if __name__ == "__main__":
    _run_demo()