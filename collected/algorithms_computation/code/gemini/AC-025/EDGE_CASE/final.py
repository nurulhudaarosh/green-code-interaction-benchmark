def solve_stage_optimization(stages, max_budget, max_memory):
    """
    Solves the multi-stage resource allocation problem under budget and memory limits.
    
    Handles edge cases:
    - N = 0 (empty stages list): Returns (0, ())
    - Empty stage options (stage with 0 choices): Returns (-1, ())
    - Max budget or memory equal to 0: Correctly evaluated
    - Infeasible allocations: Returns (-1, ())
    
    :param stages: List of stages, where each stage is a list of tuples (cost, memory, score)
    :param max_budget: Upper limit for total budget (int >= 0)
    :param max_memory: Upper limit for total memory (int >= 0)
    :return: Tuple of (max_score, optimal_choices_tuple)
    """
    # Edge case 1: Zero stages
    if not stages:
        return 0, ()

    # Edge case 2: Any stage has 0 choices (disconnected / impossible path)
    if any(len(stage) == 0 for stage in stages):
        return -1, ()

    N = len(stages)
    NEG_INF = float('-inf')

    # dp_layers[i][b][m] stores max score achievable from stage i..N-1 with remaining budget b and memory m
    dp_layers = [None] * (N + 1)
    
    # Base layer at stage N (after processing all stages): score 0
    dp_layers[N] = [[0] * (max_memory + 1) for _ in range(max_budget + 1)]

    # Backward DP pass
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

    # Forward deterministic reconstruction for lexicographically smallest choice vector
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
            return -1, ()

    return max_score, tuple(choice_vector)


# Verification & Edge Case Test Suite
def run_tests():
    # Test 1: Standard case with lexicographical tie-breaking
    # Options 0 and 1 at Stage 0 give equal scores with equal cost/mem; option 0 must be chosen.
    stages_1 = [
        [(10, 10, 50), (10, 10, 50)],
        [(5, 5, 20)]
    ]
    assert solve_stage_optimization(stages_1, 15, 15) == (70, (0, 0))

    # Test 2: Smallest permitted input (N = 0)
    assert solve_stage_optimization([], 100, 100) == (0, ())

    # Test 3: Disconnected / empty stage option structure
    stages_empty_stage = [[(1, 1, 10)], [], [(2, 2, 20)]]
    assert solve_stage_optimization(stages_empty_stage, 10, 10) == (-1, ())

    # Test 4: Zero budget and zero memory constraint
    stages_zero_cost = [
        [(0, 0, 10), (1, 0, 20)],
        [(0, 0, 15), (0, 1, 30)]
    ]
    assert solve_stage_optimization(stages_zero_cost, 0, 0) == (25, (0, 0))

    # Test 5: Infeasible constraints
    stages_infeasible = [[(10, 10, 100)]]
    assert solve_stage_optimization(stages_infeasible, 5, 5) == (-1, ())

    print("All test cases passed successfully!")


if __name__ == "__main__":
    run_tests()