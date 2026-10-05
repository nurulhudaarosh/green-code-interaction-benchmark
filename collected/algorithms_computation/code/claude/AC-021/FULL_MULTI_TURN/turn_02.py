for i in range(len(nums) - 1, -1, -1):
    a = nums[i]
    if a > target:
        continue
    for s in range(target, a - 1, -1):
        if not reach[s - a]:
            continue
        prev = dp[s - a]
        prev_count = prev[0] if prev else 0
        cur = dp[s]
        if not reach[s] or prev_count + 1 <= cur[0]:
            dp[s] = (prev_count + 1, i, prev)
            reach[s] = True