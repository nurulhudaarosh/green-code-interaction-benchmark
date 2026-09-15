#!/usr/bin/env python3
"""
Longest Increasing Route: longest strictly increasing subsequence,
returning the lexicographically smallest original-index sequence among
all maximum-length answers. O(n^2) DP with explicit index-sequence
tie-breaking. Standard library only, fully deterministic.

Optional feature: pass report_summary=True to additionally receive an
`operation_summary` dict counting major computational decisions made
during the DP. When report_summary is False (default), the return value
and all original behavior are unchanged from the base version.
"""

from typing import List, Tuple, Union, Dict
import sys


def lis_lex_smallest_indices(
    a: List[int],
    report_summary: bool = False
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, int]]]:
    n = len(a)

    # Decision counters (only meaningful/used when report_summary=True,
    # but computed cheaply regardless so behavior is 100% deterministic
    # and independent of the flag; the flag only controls what is
    # RETURNED, not how the algorithm runs).
    candidate_checks = 0
    length_improvements = 0
    tie_breaks = 0
    final_selection_comparisons = 0

    if n == 0:
        if report_summary:
            summary = {
                "candidate_checks": 0,
                "length_improvements": 0,
                "tie_breaks": 0,
                "final_selection_comparisons": 0,
                "total_decisions": 0,
            }
            return 0, [], summary
        return 0, []

    dp_len = [1] * n
    best_seq: List[List[int]] = [[i] for i in range(n)]

    for i in range(n):
        best_len_for_i = 1
        best_candidate: List[int] = [i]
        for j in range(i):
            candidate_checks += 1
            if a[j] < a[i]:
                candidate_len = dp_len[j] + 1
                candidate_seq = best_seq[j] + [i]
                if candidate_len > best_len_for_i:
                    best_len_for_i = candidate_len
                    best_candidate = candidate_seq
                    length_improvements += 1
                elif candidate_len == best_len_for_i:
                    if candidate_seq < best_candidate:
                        best_candidate = candidate_seq
                        tie_breaks += 1
        dp_len[i] = best_len_for_i
        best_seq[i] = best_candidate

    max_len = max(dp_len)

    overall_best: List[int] = None
    for i in range(n):
        if dp_len[i] == max_len:
            seq = best_seq[i]
            if overall_best is None:
                overall_best = seq
            else:
                final_selection_comparisons += 1
                if seq < overall_best:
                    overall_best = seq

    if report_summary:
        total_decisions = (
            candidate_checks
            + length_improvements
            + tie_breaks
            + final_selection_comparisons
        )
        summary = {
            "candidate_checks": candidate_checks,
            "length_improvements": length_improvements,
            "tie_breaks": tie_breaks,
            "final_selection_comparisons": final_selection_comparisons,
            "total_decisions": total_decisions,
        }
        return max_len, overall_best, summary

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

    # Default behavior: unchanged, two-field result.
    length, indices = lis_lex_smallest_indices(seq)
    values = [seq[i] for i in indices]

    print(f"Input sequence: {seq}")
    print(f"Max length (L): {length}")
    print(f"Chosen indices: {indices}")
    print(f"Chosen values : {values}")

    # Opt-in feature: request the operation_summary as well.
    length2, indices2, op_summary = lis_lex_smallest_indices(seq, report_summary=True)
    assert length2 == length and indices2 == indices  # original fields unchanged
    print(f"Operation summary: {op_summary}")