def solve_multi_stage_knapsack(stages, max_budget, max_memory, return_summary=False):
    """
    Solves the multi-stage 2-resource knapsack problem deterministically with
    optional operational summary metrics.

    :param stages: List of stages, where each stage is a list of tuples: (budget, memory, score)
    :param max_budget: Maximum allowed global budget (int)
    :param max_memory: Maximum allowed global memory (int)
    :param return_summary: Bool, if True returns (max_score, choice_vector, operation_summary)
                           otherwise returns (max_score, choice_vector)
    :return: (max_score, choice_vector) or (max_score, choice_vector, operation_summary)
    """
    num_stages = len(stages)
    summary_metrics = {
        "states_evaluated": 0,
        "dp_transitions": 0,
        "reconstruction_checks": 0
    }

    if num_stages == 0:
        if return_summary:
            return 0, [], summary_metrics
        return 0, []

    # dp[i][b][m] stores max score at stage i with budget b and memory m
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
                
                summary_metrics["states_evaluated"] += 1

                for cost_b, cost_m, score in stage_options:
                    summary_metrics["dp_transitions"] += 1
                    nb = b + cost_b
                    nm = m + cost_m
                    if nb <= max_budget and nm <= max_memory:
                        new_score = current_score + score
                        if new_score > dp[i + 1][nb][nm]:
                            dp[i + 1][nb][nm] = new_score

    # Find maximum achievable score
    max_score = -1
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            if dp[num_stages][b][m] > max_score:
                max_score = dp[num_stages][b][m]

    if max_score == -1:
        if return_summary:
            return None, [], summary_metrics
        return None, []

    # Reachability memoization for deterministic reconstruction
    reachable = [[[-1] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(num_stages + 1)]
    
    def can_reach_target(stage_idx, curr_b, curr_m, target_remaining):
        summary_metrics["reconstruction_checks"] += 1
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

    # Construct choice vector lexicographically
    choices = []
    curr_b, curr_m = 0, 0
    remaining_score = max_score

    for i in range(num_stages):
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

    if return_summary:
        return max_score, choices, summary_metrics
    return max_score, choices


# Example Execution
if __name__ == "__main__":
    sample_stages = [
        [(2, 3, 10), (1, 4, 10)],
        [(3, 1, 15), (2, 2, 12)],
        [(1, 1, 5),  (2, 1, 8)]
    ]
    budget_limit = 6
    memory_limit = 6

    # 1. Standard execution (unchanged original functionality)
    score, path = solve_multi_stage_knapsack(sample_stages, budget_limit, memory_limit)
    print("Standard Call:")
    print(f"Max Score: {score}, Choice Vector: {path}\n")

    # 2. Call with operational summary enabled
    score, path, summary = solve_multi_stage_knapsack(
        sample_stages, budget_limit, memory_limit, return_summary=True
    )
    print("Call with Summary Feature:")
    print(f"Max Score: {score}")
    print(f"Choice Vector: {path}")
    print(f"Operation Summary: {summary}")