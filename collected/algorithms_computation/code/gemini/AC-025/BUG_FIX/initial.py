from typing import List, Tuple, Dict, Optional

def solve_stage_selection(
    stages: List[List[Tuple[int, int, int]]], 
    max_budget: int, 
    max_memory: int
) -> Tuple[int, int, int, List[int]]:
    """
    Solves the 2-resource stage selection problem using 2D DP and deterministic reconstruction.

    Parameters:
        stages: List of stages, where each stage is a list of options (budget_cost, memory_cost, score).
        max_budget: Maximum allowed total budget.
        max_memory: Maximum allowed total memory.

    Returns:
        (max_score, used_budget, used_memory, chosen_indices)
    """
    num_stages = len(stages)
    if num_stages == 0:
        return 0, 0, 0, []

    # dp[stage][b][m] stores max score attainable at 'stage' with EXACTLY 'b' budget and 'm' memory used so far.
    # We use None to represent unreachable states.
    dp = [[ [None] * (max_memory + 1) for _ in range(max_budget + 1) ] for _ in range(num_stages + 1)]
    dp[0][0][0] = 0

    # Forward Pass: Build DP Table
    for i in range(num_stages):
        for b in range(max_budget + 1):
            for m in range(max_memory + 1):
                current_score = dp[i][b][m]
                if current_score is None:
                    continue
                
                for option_idx, (b_cost, m_cost, score) in enumerate(stages[i]):
                    nb, nm = b + b_cost, m + m_cost
                    if nb <= max_budget and nm <= max_memory:
                        new_score = current_score + score
                        if dp[i + 1][nb][nm] is None or new_score > dp[i + 1][nb][nm]:
                            dp[i + 1][nb][nm] = new_score

    # Find global maximum score reachable at final stage
    max_score = -1
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            if dp[num_stages][b][m] is not None:
                if dp[num_stages][b][m] > max_score:
                    max_score = dp[num_stages][b][m]

    if max_score == -1:
        raise ValueError("No valid combination fits within the budget and memory limits.")

    # Compute suffix optimal scores: suffix_max[i][b][m] = max score achievable from stage i to end
    # using AT MOST (max_budget - b) budget and (max_memory - m) memory remaining.
    # To enforce lexicographical tie-breaking, reconstruct from stage 0 to N-1 iteratively.
    
    # max_from_stage[i][b][m] stores max score attainable from stage i to end with remaining budget b and memory m.
    max_from_stage = [[[ -1 ] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(num_stages + 1)]
    
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            max_from_stage[num_stages][b][m] = 0

    for i in range(num_stages - 1, -1, -1):
        for b in range(max_budget + 1):
            for m in range(max_memory + 1):
                best = -1
                for b_cost, m_cost, score in stages[i]:
                    if b >= b_cost and m >= m_cost:
                        sub = max_from_stage[i + 1][b - b_cost][m - m_cost]
                        if sub != -1:
                            best = max(best, score + sub)
                max_from_stage[i][b][m] = best

    # Forward Reconstruction for Lexicographically First Choice
    curr_b, curr_m = max_budget, max_memory
    chosen_indices = []
    used_b, used_m = 0, 0

    for i in range(num_stages):
        target_score = max_from_stage[i][curr_b][curr_m]
        
        # Pick the FIRST option index that can achieve target_score
        selected_option = -1
        for option_idx, (b_cost, m_cost, score) in enumerate(stages[i]):
            if curr_b >= b_cost and curr_m >= m_cost:
                if max_from_stage[i + 1][curr_b - b_cost][curr_m - m_cost] != -1:
                    if score + max_from_stage[i + 1][curr_b - b_cost][curr_m - m_cost] == target_score:
                        selected_option = option_idx
                        used_b += b_cost
                        used_m += m_cost
                        curr_b -= b_cost
                        curr_m -= m_cost
                        break

        chosen_indices.append(selected_option)

    return max_score, used_b, used_m, chosen_indices


# Example Usage
if __name__ == "__main__":
    # Example stages with options defined as (budget_cost, memory_cost, score)
    sample_stages = [
        [(2, 3, 10), (3, 1, 12), (1, 4, 8)],   # Stage 0
        [(4, 2, 15), (2, 2, 14), (3, 3, 16)],   # Stage 1
        [(1, 1, 5),  (2, 1, 7)]                # Stage 2
    ]
    budget_limit = 7
    memory_limit = 6

    score, b_used, m_used, choices = solve_stage_selection(sample_stages, budget_limit, memory_limit)
    print(f"Maximum Score : {score}")
    print(f"Budget Used   : {b_used} / {budget_limit}")
    print(f"Memory Used   : {m_used} / {memory_limit}")
    print(f"Option Choice Vector: {choices}")