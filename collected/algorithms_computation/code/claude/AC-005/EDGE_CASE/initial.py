#!/usr/bin/env python3
"""
Longest strictly increasing subsequence (by value), returning the
lexicographically smallest sequence of ORIGINAL INDICES among all
optimal (maximum-length) answers.

Deterministic O(n^2) DP with explicit predecessor tracking and
tie-breaking by smallest predecessor index.

Standard library only. No randomness, no I/O side effects beyond
the __main__ demonstration.
"""

from typing import List, Sequence, Tuple


def longest_increasing_subsequence_indices(a: Sequence[int]) -> Tuple[int, List[int]]:
    """
    Return (length, indices) where:
      - length is the length of the longest strictly increasing
        subsequence of `a`,
      - indices is the lexicographically smallest list of original
        indices (0-based, strictly increasing order) among all
        subsequences achieving that maximum length.

    Lexicographic comparison is performed on the index sequences
    themselves (not on the values), i.e. index list I is preferred
    over J if I is lexicographically smaller as a list of ints.
    """
    n = len(a)
    if n == 0:
        return 0, []

    dp = [1] * n      # dp[i] = length of best strictly increasing
                       # subsequence ending exactly at index i
    pred = [-1] * n   # predecessor index chosen for dp[i], or -1

    for i in range(n):
        best_len = 1
        best_pred = -1
        # Scan candidates j < i in increasing order of j so that,
        # among all j achieving the maximum dp[j], we naturally
        # encounter the SMALLEST such j first. We only overwrite
        # best_pred on strict improvement of length, so the first
        # (smallest-index) j attaining the maximum length is kept.
        for j in range(i):
            if a[j] < a[i]:
                candidate_len = dp[j] + 1
                if candidate_len > best_len:
                    best_len = candidate_len
                    best_pred = j
                # if candidate_len == best_len, we keep the earlier
                # (smaller-index) predecessor already stored in
                # best_pred, since j increases monotonically here.
        dp[i] = best_len
        pred[i] = best_pred

    max_len = max(dp)

    # Choose the smallest ending index i with dp[i] == max_len.
    # Scanning left to right and taking the first match guarantees
    # the earliest possible final index, which is a necessary
    # condition for lexicographically smallest index list: a smaller
    # last index cannot be beaten by any sequence ending later,
    # because index lists are compared position-by-position from the
    # front, and reconstructing from the smallest-index predecessors
    # at every step (see loop above) makes each prefix as small as
    # possible while still reaching a max-length ending here.
    end = -1
    for i in range(n):
        if dp[i] == max_len:
            end = i
            break

    # Reconstruct by following predecessors backward, then reverse.
    seq_indices = []
    cur = end
    while cur != -1:
        seq_indices.append(cur)
        cur = pred[cur]
    seq_indices.reverse()

    return max_len, seq_indices


def _brute_force_reference(a: Sequence[int]) -> Tuple[int, List[int]]:
    """Exponential reference implementation for verification on small inputs."""
    n = len(a)
    best_len = 0
    best_idx: List[int] = []

    def rec(pos: int, last_val, chosen: List[int]):
        nonlocal best_len, best_idx
        if pos == n:
            if len(chosen) > best_len or (
                len(chosen) == best_len and chosen < best_idx
            ):
                best_len = len(chosen)
                best_idx = list(chosen)
            return
        # Option 1: skip index pos
        rec(pos + 1, last_val, chosen)
        # Option 2: take index pos, if valid
        if last_val is None or a[pos] > last_val:
            chosen.append(pos)
            rec(pos + 1, a[pos], chosen)
            chosen.pop()

    rec(0, None, [])
    return best_len, best_idx


if __name__ == "__main__":
    tests = [
        [],
        [5],
        [1, 2, 3, 4],
        [4, 3, 2, 1],
        [3, 1, 4, 1, 5, 9, 2, 6],
        [10, 9, 2, 5, 3, 7, 101, 18],
        [2, 2, 2, 2],
        [1, 3, 2, 4, 3, 5],
        [0, 1, 0, 1, 0, 1, 0, 1],
    ]

    for t in tests:
        length, idxs = longest_increasing_subsequence_indices(t)
        ref_length, ref_idxs = _brute_force_reference(t)
        values = [t[i] for i in idxs]
        status = "OK" if (length, idxs) == (ref_length, ref_idxs) else "MISMATCH"
        print(f"input={t}")
        print(f"  length={length} indices={idxs} values={values}  [{status}]")
        if status == "MISMATCH":
            print(f"  reference: length={ref_length} indices={ref_idxs}")