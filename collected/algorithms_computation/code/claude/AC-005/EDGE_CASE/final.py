#!/usr/bin/env python3
"""Longest Increasing Route — O(n^2) DP with lexicographically smallest
index-route tie-breaking, and explicit handling of empty/singleton/
disconnected inputs. Standard library only."""

from typing import List, Sequence, Tuple


def longest_increasing_subsequence_indices(a: Sequence[int]) -> Tuple[int, List[int]]:
    n = len(a)

    if n == 0:                     # smallest permitted input
        return 0, []
    if n == 1:                     # singleton route
        return 1, [0]

    dp = [1] * n
    pred = [-1] * n

    for i in range(n):
        best_len, best_pred = 1, -1
        for j in range(i):         # smallest-index j wins ties (strict '>' only)
            if a[j] < a[i]:
                cand = dp[j] + 1
                if cand > best_len:
                    best_len, best_pred = cand, j
        dp[i], pred[i] = best_len, best_pred

    max_len = max(dp)
    end = next(i for i in range(n) if dp[i] == max_len)  # smallest max-len endpoint

    idxs = []
    cur = end
    while cur != -1:
        idxs.append(cur)
        cur = pred[cur]
    idxs.reverse()
    return max_len, idxs


def _brute_force_reference(a: Sequence[int]) -> Tuple[int, List[int]]:
    n = len(a)
    best_len, best_idx = 0, []

    def rec(pos, last_val, chosen):
        nonlocal best_len, best_idx
        if pos == n:
            if len(chosen) > best_len or (len(chosen) == best_len and chosen < best_idx):
                best_len, best_idx = len(chosen), list(chosen)
            return
        rec(pos + 1, last_val, chosen)
        if last_val is None or a[pos] > last_val:
            chosen.append(pos)
            rec(pos + 1, a[pos], chosen)
            chosen.pop()

    rec(0, None, [])
    return best_len, best_idx


if __name__ == "__main__":
    tests = [
        [1, 2, 3, 4], [4, 3, 2, 1], [3, 1, 4, 1, 5, 9, 2, 6],
        [10, 9, 2, 5, 3, 7, 101, 18], [2, 2, 2, 2], [1, 3, 2, 4, 3, 5],
        [0, 1, 0, 1, 0, 1, 0, 1],
        [], [5], [7, 7, 7, 7, 7], [9, 8, 7, 6, 5], [-3],
        [5, -5], [-5, 5], [1, 2, 1, 2, 1, 2, 1],
    ]
    for t in tests:
        got = longest_increasing_subsequence_indices(t)
        ref = _brute_force_reference(t)
        print(t, "->", got, "OK" if got == ref else f"MISMATCH ref={ref}")

    assert longest_increasing_subsequence_indices([]) == (0, [])
    assert longest_increasing_subsequence_indices([5]) == (1, [0])
    assert longest_increasing_subsequence_indices([7, 7, 7, 7, 7]) == (1, [0])
    assert longest_increasing_subsequence_indices([9, 8, 7, 6, 5]) == (1, [0])
    assert longest_increasing_subsequence_indices([-5, 5]) == (2, [0, 1])
    print("All edge-case assertions passed.")