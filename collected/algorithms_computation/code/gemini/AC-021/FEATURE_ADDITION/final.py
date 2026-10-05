def min_subset_sum_indices(
    nums: list[int], target: int, return_summary: bool = False
) -> list[int] | None | dict:
    """
    Finds a subset of indices whose elements sum to `target`.
    Optimizes for minimal cardinality, then lexicographically smallest index list.

    :param nums: List of positive integers.
    :param target: Target sum.
    :param return_summary: If True, returns a dict with 'indices' and 'operation_summary'.
    """
    if target < 0:
        result = None
        summary = {"candidates_evaluated": 0, "state_updates": 0}
        return {"indices": result, "operation_summary": summary} if return_summary else result

    if target == 0:
        result = []
        summary = {"candidates_evaluated": 0, "state_updates": 0}
        return {"indices": result, "operation_summary": summary} if return_summary else result

    # dp[s] = (cardinality, index_list) for sum s
    dp = [None] * (target + 1)
    dp[0] = (0, [])

    candidates_evaluated = 0
    state_updates = 0

    for i, val in enumerate(nums):
        if val > target:
            continue

        for s in range(target, val - 1, -1):
            prev = dp[s - val]
            if prev is not None:
                candidates_evaluated += 1
                cand_card = prev[0] + 1
                cand_seq = prev[1] + [i]

                curr = dp[s]
                if curr is None:
                    dp[s] = (cand_card, cand_seq)
                    state_updates += 1
                else:
                    curr_card, curr_seq = curr
                    if (cand_card < curr_card) or (cand_card == curr_card and cand_seq < curr_seq):
                        dp[s] = (cand_card, cand_seq)
                        state_updates += 1

    result = dp[target][1] if dp[target] is not None else None
    summary = {
        "candidates_evaluated": candidates_evaluated,
        "state_updates": state_updates,
    }

    if return_summary:
        return {"indices": result, "operation_summary": summary}
    return result


# --- Verification ---
if __name__ == "__main__":
    nums = [3, 2, 5, 8, 1, 4]
    target = 9

    # 1. Standard backwards-compatible usage
    indices_only = min_subset_sum_indices(nums, target)
    print("Standard Call:", indices_only)

    # 2. Extended call with operation summary
    full_output = min_subset_sum_indices(nums, target, return_summary=True)
    print("Summary Call:", full_output)