#!/usr/bin/env python3
"""
Longest Increasing Route: longest strictly increasing subsequence,
returning the lexicographically smallest original-index sequence among
all maximum-length answers. O(n^2) DP with explicit index-sequence
tie-breaking. Standard library only, fully deterministic.
"""

from typing import List, Tuple
import sys


def lis_lex_smallest_indices(a: List[int]) -> Tuple[int, List[int]]:
    n = len(a)
    if n == 0:
        return 0, []

    dp_len = [1] * n
    best_seq: List[List[int]] = [[i] for i in range(n)]

    for i in range(n):
        best_len_for_i = 1
        best_candidate: List[int] = [i]
        for j in range(i):
            if a[j] < a[i]:
                candidate_len = dp_len[j] + 1
                candidate_seq = best_seq[j] + [i]
                # FIX: explicit total tie-break — compare on (length desc,
                # sequence asc) as a single deterministic key, so a
                # strictly longer candidate always wins, and among equal
                # lengths the lexicographically smallest index sequence
                # always wins, regardless of j iteration order.
                if (candidate_len > best_len_for_i or
                        (candidate_len == best_len_for_i and
                         candidate_seq < best_candidate)):
                    best_len_for_i = candidate_len
                    best_candidate = candidate_seq
        dp_len[i] = best_len_for_i
        best_seq[i] = best_candidate

    max_len = max(dp_len)

    overall_best: List[int] = None
    for i in range(n):
        if dp_len[i] == max_len:
            seq = best_seq[i]
            # FIX: same deterministic total-order comparison at the
            # final aggregation step.
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
        seq = [10, 9, 2, 5, 3, 7, 101, 18, 3, 8, 9]

    length, indices = lis_lex_smallest_indices(seq)
    values = [seq[i] for i in indices]

    print(f"Input sequence: {seq}")
    print(f"Max length (L): {length}")
    print(f"Chosen indices: {indices}")
    print(f"Chosen values : {values}")