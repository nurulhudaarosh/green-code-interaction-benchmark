from typing import List, Optional


def min_subset_sum_indices(a: List[int], target: int) -> Optional[List[int]]:
    """
    Return the ascending 0-based index list of a subset of `a` summing to
    `target` that has the fewest elements and, among ties, the
    lexicographically smallest index list. Return None if impossible.
    """
    if target < 0:
        return None
    if target == 0:
        return []

    n = len(a)
    INF = float("inf")

    # best[i][s] = min count using elements a[i:], summing exactly to s
    best = [[INF] * (target + 1) for _ in range(n + 1)]
    best[n][0] = 0
    for i in range(n - 1, -1, -1):
        v = a[i]
        cur, nxt = best[i], best[i + 1]
        for s in range(target + 1):
            val = nxt[s]
            if v <= s and nxt[s - v] + 1 < val:
                val = nxt[s - v] + 1
            cur[s] = val

    if best[0][target] == INF:
        return None

    # Reconstruct the lexicographically smallest optimal index list
    result: List[int] = []
    i, s, k = 0, target, best[0][target]
    while k > 0:
        for j in range(i, n):
            v = a[j]
            if v <= s and best[j + 1][s - v] == k - 1:
                result.append(j)
                i, s, k = j + 1, s - v, k - 1
                break
        else:  # unreachable if the DP is correct
            raise RuntimeError("reconstruction failed")
    return result


if __name__ == "__main__":
    tests = [
        ([3, 4, 5, 2, 7], 9),    # {4,5} -> [1,2]; {2,7} -> [3,4]; picks [1,2]
        ([1, 2, 3, 4, 5], 9),    # [3,4]
        ([5, 5, 5], 10),         # [0,1]
        ([2, 4, 6], 5),          # None
        ([1, 1, 1, 1], 0),       # []
        ([1, 2, 3, 3], 6),       # [2,3] (3+3) beats [0,1,2]
    ]
    for arr, t in tests:
        print(arr, t, "->", min_subset_sum_indices(arr, t))