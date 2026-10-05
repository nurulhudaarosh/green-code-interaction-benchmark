from typing import List, Tuple

def solve_stage_selection(
    stages: List[List[Tuple[int, int, int]]], 
    max_budget: int, 
    max_memory: int
) -> Tuple[int, int, int, List[int]]:
    """
    Solves the 2-resource stage selection problem using layered two-resource DP 
    and deterministic forward reconstruction with exact reachability matching.
    """
    num_stages = len(stages)
    if num_stages == 0:
        return 0, 0, 0, []

    # 1. Forward DP: dp[i][b][m] = max score at stage i with EXACT budget b and memory m
    dp = [[[-1] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(num_stages + 1)]
    dp[0][0][0] = 0

    for i in range(num_stages):
        for b in range(max_budget + 1):
            for m in range(max_memory + 1):
                if dp[i][b][m] == -1:
                    continue
                for b_cost, m_cost, score in stages[i]:
                    nb, nm = b + b_cost, m + m_cost
                    if nb <= max_budget and nm <= max_memory:
                        dp[i + 1][nb][nm] = max(dp[i + 1][nb][nm], dp[i][b][m] + score)

    # Global Max Score
    max_score = -1
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            if dp[num_stages][b][m] > max_score:
                max_score = dp[num_stages][b][m]

    if max_score == -1:
        raise ValueError("No valid combination fits within budget and memory limits.")

    # 2. Backward DP: back_dp[i][b][m] = max score from stage i to end with EXACT remaining budget b and memory m
    back_dp = [[[-1] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(num_stages + 1)]
    
    # Base case: at terminal stage num_stages, 0 remaining score for any remaining capacity
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            back_dp[num_stages][b][m] = 0

    for i in range(num_stages - 1, -1, -1):
        for b in range(max_budget + 1):
            for m in range(max_memory + 1):
                for b_cost, m_cost, score in stages[i]:
                    if b >= b_cost and m >= m_cost:
                        sub = back_dp[i + 1][b - b_cost][m - m_cost]
                        if sub != -1:
                            back_dp[i][b][m] = max(back_dp[i][b][m], score + sub)

    # 3. Deterministic Forward Reconstruction
    # We find the smallest lexicographical choice vector [c_0, c_1, ..., c_{N-1}]
    # that maintains feasibility to achieve max_score.
    
    chosen_indices = []
    curr_b, curr_m = 0, 0  # Accumulated consumption so far
    
    for i in range(num_stages):
        selected_option = -1
        selected_b_cost = 0
        selected_m_cost = 0
        
        # Test options in ascending order (0, 1, 2, ...) to ensure lexicographical tie-breaking
        for option_idx, (b_cost, m_cost, score) in enumerate(stages[i]):
            nb, nm = curr_b + b_cost, curr_m + m_cost
            if nb <= max_budget and nm <= max_memory:
                rem_b = max_budget - nb
                rem_m = max_memory - nm
                
                # Check if taking this option allows reaching max_score globally
                # We search over all possible remaining budget/memory allocation in back_dp
                can_reach_max = False
                for rb in range(rem_b + 1):
                    for rm in range(rem_m + 1):
                        if back_dp[i + 1][rb][rm] != -1:
                            if dp[i][curr_b][curr_m] + score + back_dp[i + 1][rb][rm] == max_score:
                                can_reach_max = True
                                break
                    if can_reach_max:
                        break
                
                if can_reach_max:
                    selected_option = option_idx
                    selected_b_cost = b_cost
                    selected_m_cost = m_cost
                    break
        
        chosen_indices.append(selected_option)
        curr_b += selected_b_cost
        curr_m += selected_m_cost

    return max_score, curr_b, curr_m, chosen_indices


if __name__ == "__main__":
    # Test Demonstration
    sample_stages = [
        [(1, 1, 10), (2, 2, 10)],  # Stage 0
        [(2, 2, 10), (1, 1, 10)]   # Stage 1
    ]
    budget_limit = 3
    memory_limit = 3

    score, b_used, m_used, choices = solve_stage_selection(sample_stages, budget_limit, memory_limit)
    print(f"Maximum Score : {score}")
    print(f"Budget Used   : {b_used} / {budget_limit}")
    print(f"Memory Used   : {m_used} / {memory_limit}")
    print(f"Option Choice Vector: {choices}")