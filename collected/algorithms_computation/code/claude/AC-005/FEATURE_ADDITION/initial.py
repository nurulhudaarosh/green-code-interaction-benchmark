"""
Lexicographically-smallest longest strictly increasing subsequence (by index).

Standard library only. No network access, no randomness, no I/O beyond the
built-in demonstration in __main__. Deterministic: identical input always
produces identical output.
"""

from typing import List, Tuple


def longest_increasing_subsequence_indices(a: List[int]) -> Tuple[List[int], List[int]]:
    """
    Given an integer sequence `a`, return (indices, values) where `indices`
    is the lexicographically smallest list of original indices i1<i2<...<ik
    such that a[i1]<a[i2]<...<a[ik] is a longest strictly increasing
    subsequence of `a`.

    "Lexicographically smallest" compares the index tuples themselves
    (i1 first, then i2, ...), among all index tuples achieving the maximum
    possible length k.

    Runs in O(n^2) time using an explicit DP table plus a deterministic
    greedy tie-breaking pass. Empty input returns ([], []).
    """
    n = len(a)
    if n == 0:
        return [], []

    # suf[i] = length of the longest strictly increasing subsequence that
    # can start at index i (restricted to indices >= i).
    suf = [1] * n
    for i in range(n - 1, -1, -1):
        best = 1
        for j in range(i + 1, n):
            if a[j] > a[i] and suf[j] + 1 > best:
                best = suf[j] + 1
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
            if suf[j] != remaining:
                continue
            if prev_val is not None and a[j] <= prev_val:
                continue
            chosen = j
            break
        # chosen is guaranteed to be found because suf[] and max_len are
        # consistent by construction of the DP.
        result_indices.append(chosen)
        prev_val = a[chosen]
        start = chosen + 1
        remaining -= 1

    result_values = [a[i] for i in result_indices]
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

    for a in test_cases:
        indices, values = longest_increasing_subsequence_indices(a)
        print(f"a       = {a}")
        print(f"indices = {indices}")
        print(f"values  = {values}")
        print(f"length  = {len(indices)}")
        print("-" * 40)


if __name__ == "__main__":
    _run_demo()