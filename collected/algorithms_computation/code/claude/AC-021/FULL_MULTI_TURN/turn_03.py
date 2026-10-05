from typing import Dict, List, Optional, Union


def min_count_lex_smallest_subset(
    nums: List[int], target: int, with_summary: bool = False
) -> Union[Optional[List[int]], Dict[str, object]]:
    """Minimum-cardinality subset sum, ties -> lexicographically smallest indices.

    Default (with_summary=False): returns exactly what it always did: the ascending
    0-based index list, [] when target == 0, or None if impossible.

    with_summary=True: returns {"indices": <same value as above>,
                                "operation_summary": {...deterministic counters...}}.
    Raises ValueError/TypeError on invalid input (non-int, non-positive element,
    negative target), regardless of with_summary.
    """
    if isinstance(target, bool) or not isinstance(target, int) or target < 0:
        raise ValueError("target must be a non-negative integer")
    for a in nums:
        if isinstance(a, bool) or not isinstance(a, int):
            raise TypeError("all elements must be integers")
        if a <= 0:
            raise ValueError("all elements must be positive integers")

    # Counters (pure bookkeeping; they never influence the algorithm).
    c_items = len(nums)
    c_items_skipped = 0        # items larger than target, skipped whole
    c_examined = 0             # (item, sum) transitions examined
    c_unreachable = 0          # skipped: dp[s-a] unreachable
    c_first_reach = 0          # sum s reached for the first time
    c_improved = 0             # strictly fewer elements than existing dp[s]
    c_tie_replaced = 0         # equal count; smaller index list wins
    c_rejected = 0             # candidate worse (more elements); dp[s] kept
    c_reconstruct = 0          # nodes followed during reconstruction

    def summary(result):
        total = c_items_skipped + c_examined + c_reconstruct
        return {
            "indices": result,
            "operation_summary": {
                "items_total": c_items,
                "items_skipped_too_large": c_items_skipped,
                "transitions_examined": c_examined,
                "skipped_unreachable": c_unreachable,
                "first_time_reached": c_first_reach,
                "strict_improvements": c_improved,
                "tie_replacements": c_tie_replaced,
                "candidates_rejected": c_rejected,
                "reconstruction_steps": c_reconstruct,
                "total_decisions": total,
            },
        }

    if target == 0:
        return summary([]) if with_summary else []

    dp: List[Optional[tuple]] = [None] * (target + 1)   # (count, index, parent)
    reach = [False] * (target + 1)
    reach[0] = True

    for i in range(len(nums) - 1, -1, -1):
        a = nums[i]
        if a > target:
            c_items_skipped += 1
            continue
        for s in range(target, a - 1, -1):               # descending => 0/1 use
            c_examined += 1
            if not reach[s - a]:
                c_unreachable += 1
                continue
            prev = dp[s - a]
            prev_count = prev[0] if prev else 0
            if not reach[s]:
                dp[s] = (prev_count + 1, i, prev)
                reach[s] = True
                c_first_reach += 1
            else:
                cur_count = dp[s][0]
                if prev_count + 1 < cur_count:
                    dp[s] = (prev_count + 1, i, prev)
                    c_improved += 1
                elif prev_count + 1 == cur_count:
                    dp[s] = (prev_count + 1, i, prev)    # i < all indices in dp[s]
                    c_tie_replaced += 1
                else:
                    c_rejected += 1

    node = dp[target]
    result: Optional[List[int]] = None
    if node is not None:
        result = []
        while node is not None:
            result.append(node[1])
            node = node[2]
            c_reconstruct += 1
    return summary(result) if with_summary else result


if __name__ == "__main__":
    import itertools, random
    f = min_count_lex_smallest_subset

    def brute(nums, t):
        for k in range(len(nums) + 1):
            for c in itertools.combinations(range(len(nums)), k):
                if sum(nums[i] for i in c) == t:
                    return list(c)
        return None

    # Original behaviour unchanged when feature is off / not requested.
    for nums, t, exp in [([3, 34, 4, 12, 5, 2], 9, [2, 4]), ([1, 2, 3, 4], 5, [0, 3]),
                         ([5, 5, 5], 10, [0, 1]), ([2, 4, 6], 5, None), ([7], 0, []),
                         ([1, 1, 1, 1, 4], 4, [4]), ([2, 3, 1, 4], 5, [0, 1])]:
        assert f(nums, t) == exp and f(nums, t, with_summary=False) == exp
        assert f(nums, t, with_summary=True)["indices"] == exp

    random.seed(11)  # self-test only
    for _ in range(20000):
        nums = [random.randint(1, 8) for _ in range(random.randint(0, 9))]
        t = random.randint(0, 30)
        plain = f(nums, t)
        rich = f(nums, t, with_summary=True)
        assert plain == brute(nums, t) == rich["indices"]
        assert rich == f(nums, t, with_summary=True)            # deterministic
        o = rich["operation_summary"]
        assert o["transitions_examined"] == (o["skipped_unreachable"] + o["first_time_reached"]
            + o["strict_improvements"] + o["tie_replacements"] + o["candidates_rejected"])
        assert o["reconstruction_steps"] == (len(plain) if plain else 0)
        assert o["total_decisions"] == (o["items_skipped_too_large"]
            + o["transitions_examined"] + o["reconstruction_steps"])

    print(f([1, 2, 3, 4], 5, with_summary=True))
    print("all tests passed")