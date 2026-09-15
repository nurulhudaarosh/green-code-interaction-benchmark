#!/usr/bin/env python3
"""
Longest Strictly Increasing Subsequence with lexicographically smallest
index sequence among all optimal (maximum-length) answers.

Deterministic O(n^2) DP. Standard library only. No I/O side effects beyond
stdin/stdout in the __main__ block.
"""

from typing import List, Tuple
import sys


def lis_lex_smallest_indices(a: List[int]) -> Tuple[int, List[int]]:
    """
    Given a list of integers `a`, find the maximum length L of a strictly
    increasing subsequence, and return (L, indices) where `indices` is the
    lexicographically smallest list of original indices (as a sequence of
    ints, compared element-by-element) among all index sequences that
    achieve length L and correspond to a valid strictly increasing
    subsequence.

    Returns (0, []) for an empty input.
    """
    n = len(a)
    if n == 0:
        return 0, []

    # dp_len[i]  = length of best strictly increasing subsequence ending at i
    # best_seq[i] = lexicographically smallest index-sequence of that length
    #               ending exactly at index i
    dp_len = [1] * n
    best_seq: List[List[int]] = [[i] for i in range(n)]

    for i in range(n):
        best_len_for_i = 1
        best_candidate: List[int] = [i]
        for j in range(i):
            if a[j] < a[i]:
                candidate_len = dp_len[j] + 1
                candidate_seq = best_seq[j] + [i]
                if candidate_len > best_len_for_i:
                    best_len_for_i = candidate_len
                    best_candidate = candidate_seq
                elif candidate_len == best_len_for_i:
                    if candidate_seq < best_candidate:
                        best_candidate = candidate_seq
        dp_len[i] = best_len_for_i
        best_seq[i] = best_candidate

    max_len = max(dp_len)

    overall_best: List[int] = None
    for i in range(n):
        if dp_len[i] == max_len:
            seq = best_seq[i]
            if overall_best is None or seq < overall_best:
                overall_best = seq

    return max_len, overall_best


def _read_ints_from_stdin() -> List[int]:
    data = sys.stdin.read().split()
    return [int(x) for x in data]


if __name__ == "__main__":
    if not sys.stdin.isatty():
        raw = _read_ints_from_stdin()
    else:
        raw = []

    if raw:
        seq = raw
    else:
        # Deterministic built-in example if no stdin input is provided.
        seq = [10, 9, 2, 5, 3, 7, 101, 18, 3, 8, 9]

    length, indices = lis_lex_smallest_indices(seq)
    values = [seq[i] for i in indices]

    print(f"Input sequence: {seq}")
    print(f"Max length (L): {length}")
    print(f"Chosen indices: {indices}")
    print(f"Chosen values : {values}")