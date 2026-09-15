#!/usr/bin/env python3
"""
Longest Strictly Increasing Subsequence (LIS) with lexicographically
smallest original-index sequence among all optimal-length answers.

O(n^2) DP with explicit predecessor tracking AND explicit best-path
tracking per index, using canonical backward reconstruction to
guarantee deterministic, provably-correct lexicographic minimality.
Standard library only. No randomness, no I/O side effects beyond
stdin/stdout in main().
"""

from typing import List, Sequence, Tuple, Optional


def lis_lex_smallest_indices(a: Sequence[int]) -> Tuple[int, List[int]]:
    """
    Returns (max_length, indices): the lexicographically smallest list of
    original indices (strictly increasing indices, strictly increasing
    values) achieving the maximum strictly-increasing-subsequence length.

    DP definition:
      dp_len[i]  = length of the best strictly increasing subsequence
                   ending exactly at index i.
      pred[i]    = the chosen predecessor index j (or None) used to
                   reconstruct the lexicographically smallest path
                   ending at i among all paths of length dp_len[i].

    Tie-breaking rule (explicit, deterministic):
      For each i, scan j = 0 .. i-1 in increasing order. A candidate j
      is usable if a[j] < a[i]. Track the best achievable length
      candidate_len = dp_len[j] + 1. We select the predecessor that:
        1. maximizes candidate_len (primary criterion), and
        2. among predecessors achieving the maximal candidate_len,
           minimizes the resulting path dp_path[j] + [i] lexicographically
           (secondary criterion), where dp_path[j] is itself the already
           finalized (proven lexicographically smallest) path ending at j.
      This is correct by induction: dp_path[j] for j < i is already the
      unique lexicographically smallest path of length dp_len[j] ending
      at j (proven at the time j was processed), so comparing
      dp_path[j] + [i] across candidate j's correctly finds the
      lexicographically smallest path of length dp_len[i] ending at i.

    Final selection: among all i with dp_len[i] == max_len, pick the
    smallest dp_path[i] lexicographically. This is valid because any
    optimal subsequence must end at some index i achieving max_len, and
    dp_path[i] is already the lex-smallest path of that length ending
    there.
    """
    n = len(a)
    if n == 0:
        return 0, []

    dp_len: List[int] = [1] * n
    pred: List[Optional[int]] = [None] * n
    dp_path: List[List[int]] = [[i] for i in range(n)]

    for i in range(n):
        best_len = 1
        best_pred: Optional[int] = None
        best_path: List[int] = [i]

        for j in range(i):
            if a[j] < a[i]:
                candidate_len = dp_len[j] + 1
                candidate_path = dp_path[j] + [i]
                if candidate_len > best_len:
                    best_len = candidate_len
                    best_pred = j
                    best_path = candidate_path
                elif candidate_len == best_len and candidate_path < best_path:
                    best_pred = j
                    best_path = candidate_path

        dp_len[i] = best_len
        pred[i] = best_pred
        dp_path[i] = best_path

    max_len = max(dp_len)

    best_end: Optional[int] = None
    best_overall_path: Optional[List[int]] = None
    for i in range(n):
        if dp_len[i] == max_len:
            if best_overall_path is None or dp_path[i] < best_overall_path:
                best_overall_path = dp_path[i]
                best_end = i

    # Explicit predecessor-based reconstruction (defensive cross-check
    # against dp_path, guaranteeing the "explicit predecessor" requirement
    # is genuinely enforced, not just implied by stored paths).
    reconstructed: List[int] = []
    cur = best_end
    while cur is not None:
        reconstructed.append(cur)
        cur = pred[cur]
    reconstructed.reverse()

    assert reconstructed == best_overall_path, (
        "Predecessor reconstruction diverged from stored path; "
        "tie-breaking is not deterministic."
    )

    return max_len, best_overall_path


def main() -> None:
    test_cases: List[List[int]] = [
        [],
        [5],
        [3, 3, 3, 3],
        [10, 9, 2, 5, 3, 7, 101, 18],
        [0, 1, 0, 3, 2, 3],
        [7, 7, 7, 7, 7, 7, 7],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [2, 2, 2, 1, 3, 1, 3, 2, 4],
        [2, 1, 3],
        [1, 3, 2, 3],
        [3, 1, 2, 4],
        [2, 3, 1],
    ]

    for a in test_cases:
        length, indices = lis_lex_smallest_indices(a)
        values = [a[i] for i in indices]
        print(f"a = {a}")
        print(f"  max_length = {length}")
        print(f"  indices    = {indices}")
        print(f"  values     = {values}")
        print()


if __name__ == "__main__":
    main()