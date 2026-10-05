from typing import List, Optional

def subset_sum_optimal(nums: List[int], target: int) -> Optional[List[int]]:
    """
    Returns a list of 0-based indices forming a subset of nums that sums to target,
    minimizing first the number of elements, then lexicographically smallest index list.
    Returns None if no such subset exists.
    """
    n = len(nums)
    INF = float('inf')

    # min_count[s] = minimum number of elements to reach sum s
    min_count = [INF] * (target + 1)
    min_count[0] = 0

    # choice[s] = index of the last element used to reach sum s optimally
    choice = [-1] * (target + 1)

    for i, val in enumerate(nums):
        if val > target:
            continue
        # Iterate downward to ensure each element used at most once
        for s in range(target, val - 1, -1):
            if min_count[s - val] + 1 < min_count[s]:
                min_count[s] = min_count[s - val] + 1
                choice[s] = i

    if min_count[target] == INF:
        return None

    # Reconstruct indices
    indices = []
    s = target
    while s > 0:
        i = choice[s]
        if i == -1:
            return None  # should not happen if min_count[target] is finite
        indices.append(i)
        s -= nums[i]

    indices.reverse()
    return indices


if __name__ == "__main__":
    # Example usage
    nums = [3, 34, 4, 12, 5, 2]
    target = 9
    result = subset_sum_optimal(nums, target)
    if result is None:
        print("No subset sums to target.")
    else:
        print("Indices:", result)
        print("Values:", [nums[i] for i in result])
        print("Sum:", sum(nums[i] for i in result))
        print("Count:", len(result))