"""
PROBLEM
    Given positive integers `nums` (identified by index; duplicates are distinct
    items) and a target T, decide whether a subset sums exactly to T.
    If possible, choose the subset with the FEWEST elements; among those, choose
    the one whose sorted index list is LEXICOGRAPHICALLY SMALLEST.

CONSTRAINTS
    - Each element used at most once (0/1).
    - Values are positive integers, T >= 0.

OUTPUT
    Sorted list of indices, or None if T is unreachable. T == 0 -> [].

ALGORITHM
    0/1 subset-sum DP over sums 0..T. dp[s] = (count, index_tuple): best way to
    reach sum s using items i..n-1.
      * Process items right-to-left, so prepending index i keeps tuples sorted.
      * Iterate s downward (T..a) so each item is used at most once.
      * Compare (count, tuple): fewest elements first, then lexicographic order.
    Time O(n*T*k), memory O(T*k), where k is the answer size.
"""

from itertools import combinations, product


def min_card_lex_subset(nums, target):
    if target < 0:
        return None
    dp = [None] * (target + 1)
    dp[0] = (0, ())
    for i in range(len(nums) - 1, -1, -1):
        a = nums[i]
        if a <= 0 or a > target:
            continue
        for s in range(target, a - 1, -1):
            prev = dp[s - a]
            if prev is None:
                continue
            cand = (prev[0] + 1, (i,) + prev[1])
            cur = dp[s]
            if cur is None or cand < cur:
                dp[s] = cand
    return None if dp[target] is None else list(dp[target][1])


def _brute(nums, target):
    for k in range(len(nums) + 1):
        for c in combinations(range(len(nums)), k):  # lexicographic order
            if sum(nums[i] for i in c) == target:
                return list(c)
    return None


def _self_test():
    for n in range(6):
        for nums in product(range(1, 5), repeat=n):
            for t in range(15):
                assert min_card_lex_subset(list(nums), t) == _brute(list(nums), t), (nums, t)


if __name__ == "__main__":
    _self_test()
    print(min_card_lex_subset([3, 34, 4, 12, 5, 2], 9))  # [2, 4]
    print(min_card_lex_subset([5, 5, 10, 2, 3], 10))     # [2]
    print(min_card_lex_subset([1, 2, 3], 7))             # None
    print(min_card_lex_subset([4, 6], 0))                # []