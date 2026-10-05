def solve_stage_selection(stages, max_budget, max_memory):
    """
    Solves the multi-stage resource-constrained option selection problem.
    
    stages: List of stages, where each stage is a list of options.
            Each option is a dict or tuple: (budget_cost, memory_cost, score)
    max_budget: int
    max_memory: int
    
    Returns: (max_score, chosen_indices)
    """
    num_stages = len(stages)
    
    # dp[b][m] stores (max_score, choice_path_tuple)
    # We initialize DP layer 0 with budget=0, memory=0, score=0, path=()
    dp = {}
    dp[(0, 0)] = (0, ())

    for stage_idx, stage_options in enumerate(stages):
        next_dp = {}
        for (b, m), (score, path) in dp.items():
            for opt_idx, (b_cost, m_cost, opt_score) in enumerate(stage_options):
                nb = b + b_cost
                nm = m + m_cost
                
                if nb <= max_budget and nm <= max_memory:
                    new_score = score + opt_score
                    new_path = path + (opt_idx,)
                    
                    if (nb, nm) not in next_dp:
                        next_dp[(nb, nm)] = (new_score, new_path)
                    else:
                        curr_score, curr_path = next_dp[(nb, nm)]
                        # Maximize score; on tie, choose lexicographically smaller path
                        if new_score > curr_score:
                            next_dp[(nb, nm)] = (new_score, new_path)
                        elif new_score == curr_score:
                            if new_path < curr_path:
                                next_dp[(nb, nm)] = (new_score, new_path)
        dp = next_dp

    if not dp:
        return None, []  # Infeasible constraints

    # Global search for maximum score across all feasible (b, m) states
    best_score = -1
    best_path = None

    for (score, path) in dp.values():
        if score > best_score:
            best_score = score
            best_path = path
        elif score == best_score:
            if best_path is None or path < best_path:
                best_path = path

    return best_score, list(best_path)


# Example Verification
if __name__ == "__main__":
    # Stage options format: (budget, memory, score)
    sample_stages = [
        [(2, 3, 10), (1, 5, 12), (3, 2, 11)],  # Stage 0
        [(4, 1, 15), (2, 2, 20)],              # Stage 1
        [(1, 1, 5),  (3, 3, 12)]               # Stage 2
    ]
    budget_limit = 7
    memory_limit = 7

    max_score, selections = solve_stage_selection(sample_stages, budget_limit, memory_limit)
    print(f"Optimal Total Score: {max_score}")
    print(f"Selected Options Vector: {selections}")