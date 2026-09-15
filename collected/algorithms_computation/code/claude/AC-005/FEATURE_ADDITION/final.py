"""
Lexicographically-smallest longest strictly increasing subsequence (by index),
with an optional deterministic operation_summary feature.

Standard library only. No network access, no randomness, no external I/O
beyond the built-in __main__ demonstration. Deterministic: identical input
always produces identical output.
"""

from typing import List, Tuple, Dict, Union


def longest_increasing_subsequence_indices(
    a: List[int],
    include_operation_summary: bool = False,
) -> Union[Tuple[List[int], List[int]], Tuple[List[int], List[int], Dict[str, int]]]:
    """
    Given an integer sequence `a`, return the lexicographically smallest list
    of original indices i1<i2<...<ik such that a[i1]<a[i2]<...<a[ik] is a
    longest strictly increasing subsequence of `a`.

    Default behavior (include_operation_summary=False) is UNCHANGED from the
    original solution:
        returns (indices, values)

    When include_operation_summary=True, an additional third element is
    returned:
        returns (indices, values, operation_summary)
    where operation_summary is a dict of deterministic counters describing
    the number of major computational decisions/operations performed:
        - dp_comparisons     : value comparisons made while filling the DP table
        - dp_updates         : number of times a DP entry was improved
        - greedy_scan_steps  : index positions examined during reconstruction
        - greedy_picks       : indices chosen (== LIS length)
        - total_operations   : sum of the four counters above

    Runs in O(n^2) time. Empty input returns ([], []) or ([], [], summary)
    with all-zero counters, depending on the flag.
    """
    n = len(a)

    # --- Operation counters (all major decision points are tallied here) ---
    dp_comparisons = 0
    dp_updates = 0
    greedy_scan_steps = 0
    greedy_picks = 0

    if n == 0:
        indices, values = [], []
        if include_operation_summary:
            summary = {
                "dp_comparisons": 0,
                "dp_updates": 0,
                "greedy_scan_steps": 0,
                "greedy_picks": 0,
                "total_operations": 0,
            }
            return indices, values, summary
        return indices, values

    # suf[i] = length of the longest strictly increasing subsequence that
    # can start at index i (restricted to indices >= i).
    suf = [1] * n
    for i in range(n - 1, -1, -1):
        best = 1
        for j in range(i + 1, n):
            dp_comparisons += 1  # major decision: compare a[j] > a[i]
            if a[j] > a[i] and suf[j] + 1 > best:
                best = suf[j] + 1
                dp_updates += 1  # major decision: improved DP entry
        suf[i] = best

    max_len = max(suf)

    # Greedy left-to-right reconstruction of the lexicographically smallest
    # index tuple among all optimal (max_len) strictly increasing subsequences.
    result_indices: List[int] = []
    remaining = max_len
    start = 0
    prev_val = None  # None acts as -infinity for the first pick

    while remaining > 0:
        chosen = -1
        for j in range(start, n):
            greedy_scan_steps += 1  # major decision: examine candidate index j
            if suf[j] != remaining:
                continue
            if prev_val is not None and a[j] <= prev_val:
                continue
            chosen = j
            break
        result_indices.append(chosen)
        greedy_picks += 1  # major decision: commit to index `chosen`
        prev_val = a[chosen]
        start = chosen + 1
        remaining -= 1

    result_values = [a[i] for i in result_indices]

    if include_operation_summary:
        total_operations = dp_comparisons + dp_updates + greedy_scan_steps + greedy_picks
        summary = {
            "dp_comparisons": dp_comparisons,
            "dp_updates": dp_updates,
            "greedy_scan_steps": greedy_scan_steps,
            "greedy_picks": greedy_picks,
            "total_operations": total_operations,
        }
        return result_indices, result_values, summary

    return result_indices, result_values


def _run_demo() -> None:
    test_cases = [
        [],
        [5],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [3, 10, 2, 1, 20],
        [10, 9, 2, 5, 3, 7, 101, 18],
        [2, 2, 2, 2],
        [1, 3, 6, 7, 9, 4, 10, 5, 6],
        [0, 1, 0, 3, 2, 3],
        [-5, -1, -2, 0, 4, 3, 5],
    ]

    print("=== Default behavior (feature disabled, unchanged) ===")
    for a in test_cases:
        indices, values = longest_increasing_subsequence_indices(a)
        print(f"a       = {a}")
        print(f"indices = {indices}")
        print(f"values  = {values}")
        print(f"length  = {len(indices)}")
        print("-" * 40)

    print("\n=== With operation_summary (feature enabled) ===")
    for a in test_cases:
        indices, values, summary = longest_increasing_subsequence_indices(
            a, include_operation_summary=True
        )
        print(f"a               = {a}")
        print(f"indices         = {indices}")
        print(f"values          = {values}")
        print(f"operation_summary = {summary}")
        print("-" * 40)


if __name__ == "__main__":
    _run_demo()