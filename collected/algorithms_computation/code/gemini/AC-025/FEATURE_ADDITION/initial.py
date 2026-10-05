def solve_multi_stage_knapsack(stages, max_budget, max_memory):
    """
    Solves the multi-stage 2-resource knapsack problem deterministically.

    :param stages: List of stages, where each stage is a list of tuples: (budget, memory, score)
    :param max_budget: Maximum allowed global budget (int)
    :param max_memory: Maximum allowed global memory (int)
    :return: Tuple (max_score, choice_vector)
    """
    num_stages = len(stages)
    if num_stages == 0:
        return 0, []

    # dp[i][b][m] stores max score at stage i with budget b and memory m
    # Initialize with -1 to represent unreachable states
    dp = [[[-1] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(num_stages + 1)]
    dp[0][0][0] = 0

    # Forward DP Pass
    for i in range(num_stages):
        stage_options = stages[i]
        for b in range(max_budget + 1):
            for m in range(max_memory + 1):
                current_score = dp[i][b][m]
                if current_score == -1:
                    continue
                
                for cost_b, cost_m, score in stage_options:
                    nb = b + cost_b
                    nm = m + cost_m
                    if nb <= max_budget and nm <= max_memory:
                        if current_score + score > dp[i + 1][nb][nm]:
                            dp[i + 1][nb][nm] = current_score + score

    # Find the maximum achievable score at stage N across all valid (b, m)
    max_score = -1
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            if dp[num_stages][b][m] > max_score:
                max_score = dp[num_stages][b][m]

    if max_score == -1:
        return None, []  # No valid assignment possible

    # Reconstruction with Lexicographical Tie-Breaking
    # To find the lexicographically smallest sequence of option indices,
    # we reconstruct forward using a helper to check reachability to max_score.

    # Reachable matrix to prune invalid reconstruction paths
    # reachable[i][b][m] = True if state (b,m) at stage i can achieve max_score at the end
    reachable = [[[-1] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(num_stages + 1)]
    
    def can_reach_target(stage_idx, curr_b, curr_m, target_remaining):
        if stage_idx == num_stages:
            return target_remaining == 0
        if reachable[stage_idx][curr_b][curr_m] != -1:
            return reachable[stage_idx][curr_b][curr_m] == 1

        res = False
        if dp[stage_idx][curr_b][curr_m] != -1:
            for cost_b, cost_m, score in stages[stage_idx]:
                nb, nm = curr_b + cost_b, curr_m + cost_m
                if nb <= max_budget and nm <= max_memory and score <= target_remaining:
                    if dp[stage_idx + 1][nb][nm] >= dp[stage_idx][curr_b][curr_m] + score:
                        if can_reach_target(stage_idx + 1, nb, nm, target_remaining - score):
                            res = True
                            break
        reachable[stage_idx][curr_b][curr_m] = 1 if res else 0
        return res

    # Construct choices lexicographically
    choices = []
    curr_b, curr_m = 0, 0
    remaining_score = max_score

    for i in range(num_stages):
        # Iterate options in natural order (0-indexed) for lexicographical smallest choice
        for opt_idx, (cost_b, cost_m, score) in enumerate(stages[i]):
            nb, nm = curr_b + cost_b, curr_m + cost_m
            if nb <= max_budget and nm <= max_memory and score <= remaining_score:
                if dp[i + 1][nb][nm] == dp[i][curr_b][curr_m] + score:
                    if can_reach_target(i + 1, nb, nm, remaining_score - score):
                        choices.append(opt_idx)
                        curr_b = nb
                        curr_m = nm
                        remaining_score -= score
                        break

    return max_score, choices


# Example Usage / Verification
if __name__ == "__main__":
    # Stage options format: [(budget, memory, score), ...]
    sample_stages = [
        [(2, 3, 10), (1, 4, 10)],  # Stage 0: options 0 and 1 give same score, option 1 costs less budget
        [(3, 1, 15), (2, 2, 12)],  # Stage 1
        [(1, 1, 5),  (2, 1, 8)]    # Stage 2
    ]
    budget_limit = 6
    memory_limit = 6

    score, path = solve_multi_stage_knapsack(sample_stages, budget_limit, memory_limit)
    print(f"Max Score: {score}")
    print(f"Selected Choices (0-indexed per stage): {path}")