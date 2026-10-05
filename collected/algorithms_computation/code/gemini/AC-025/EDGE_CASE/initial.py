def solve_stage_optimization(stages, max_budget, max_memory):
    """
    Solves the multi-stage resource allocation problem under budget and memory limits.
    
    :param stages: List of stages, where each stage is a list of tuples (cost, memory, score)
    :param max_budget: Upper limit for total budget (int)
    :param max_memory: Upper limit for total memory (int)
    :return: Tuple of (max_score, optimal_choices_tuple)
             Returns (-1, ()) if no feasible solution exists.
    """
    N = len(stages)
    NEG_INF = float('-inf')

    # Compute Suffix DP tables to enable deterministic lexicographical forward-reconstruction
    # suffix_dp[i][b][m] = max score achievable from stage i..N-1 given budget b and memory m
    suffix_dp = [[NEG_INF] * (max_memory + 1) for _ in range(max_budget + 1)]
    
    # Base case for suffix DP: after all stages (stage N), 0 remaining stages gives score 0
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            suffix_dp[b][m] = 0

    # Store backward DP tables for each stage threshold
    # tables[i][b][m] stores suffix_dp at stage i
    dp_layers = [None] * (N + 1)
    dp_layers[N] = suffix_dp

    for i in range(N - 1, -1, -1):
        prev_layer = dp_layers[i + 1]
        curr_layer = [[NEG_INF] * (max_memory + 1) for _ in range(max_budget + 1)]
        
        for b in range(max_budget + 1):
            for m in range(max_memory + 1):
                best = NEG_INF
                for cost, mem, score in stages[i]:
                    if b >= cost and m >= mem:
                        sub = prev_layer[b - cost][m - mem]
                        if sub != NEG_INF:
                            cand = score + sub
                            if cand > best:
                                best = cand
                curr_layer[b][m] = best
        dp_layers[i] = curr_layer

    max_score = dp_layers[0][max_budget][max_memory]
    if max_score == NEG_INF:
        return -1, ()  # Infeasible

    # Deterministic reconstruction: greedily pick smallest choice index j at each stage
    choice_vector = []
    curr_b = max_budget
    curr_m = max_memory
    target_score = max_score

    for i in range(N):
        next_layer = dp_layers[i + 1]
        chosen = False
        
        for j, (cost, mem, score) in enumerate(stages[i]):
            if curr_b >= cost and curr_m >= mem:
                remaining_b = curr_b - cost
                remaining_m = curr_m - mem
                if next_layer[remaining_b][remaining_m] != NEG_INF:
                    if score + next_layer[remaining_b][remaining_m] == target_score:
                        choice_vector.append(j)
                        curr_b -= cost
                        curr_m -= mem
                        target_score -= score
                        chosen = True
                        break
        if not chosen:
            raise RuntimeError("Reconstruction failed to match optimal score.")

    return max_score, tuple(choice_vector)


# Example usage:
if __name__ == "__main__":
    # Stage 0: 2 options -> (cost, memory, score)
    # Stage 1: 2 options
    sample_stages = [
        [(10, 20, 100), (15, 10, 110)],  # Stage 0
        [(20, 30, 150), (10, 40, 140)]   # Stage 1
    ]
    budget_limit = 30
    memory_limit = 50

    score, vector = solve_stage_optimization(sample_stages, budget_limit, memory_limit)
    print(f"Maximum Score: {score}")
    print(f"Optimal Option Vector: {vector}")