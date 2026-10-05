from typing import List, Tuple, Optional

class Option:
    def __init__(self, budget: int, memory: int, score: int):
        self.budget = budget
        self.memory = memory
        self.score = score

def solve_mckp_2d(
    stages: List[List[Option]], 
    max_budget: int, 
    max_memory: int
) -> Optional[Tuple[int, int, int, List[int]]]:
    """
    Solves 2D Multiple-Choice Knapsack Problem using layered 2D dynamic programming
    and deterministic reconstruction with lexicographical tie-breaking.
    
    Returns:
        (max_score, used_budget, used_memory, choice_indices) or None if infeasible.
    """
    N = len(stages)
    if N == 0:
        return 0, 0, 0, []

    # dp[i][b][m] stores max score achievable at stage i using exactly b budget and m memory
    # Initialize DP table with -1 (unreachable state)
    dp = [[[-1] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(N)]

    # Stage 0 initialization
    for opt_idx, opt in enumerate(stages[0]):
        if opt.budget <= max_budget and opt.memory <= max_memory:
            if opt.score > dp[0][opt.budget][opt.memory]:
                dp[0][opt.budget][opt.memory] = opt.score

    # Forward DP Pass for Stages 1 to N-1
    for i in range(1, N):
        for b in range(max_budget + 1):
            for m in range(max_memory + 1):
                prev_score = dp[i - 1][b][m]
                if prev_score == -1:
                    continue

                for opt in stages[i]:
                    nb = b + opt.budget
                    nm = m + opt.memory
                    if nb <= max_budget and nm <= max_memory:
                        new_score = prev_score + opt.score
                        if new_score > dp[i][nb][nm]:
                            dp[i][nb][nm] = new_score

    # Find global maximum score at final stage N-1
    max_score = -1
    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            if dp[N - 1][b][m] > max_score:
                max_score = dp[N - 1][b][m]

    if max_score == -1:
        return None  # Infeasible

    # Deterministic Reconstruction for Lexicographically Smallest Choice Vector
    # We find all feasible (b_final, m_final) pairs that yield max_score,
    # and reconstruct choice vectors to find the lexicographically smallest.
    
    def reconstruct(stage_idx: int, rem_b: int, rem_m: int) -> Optional[List[int]]:
        """Reconstructs choices for stages 0..stage_idx reaching (rem_b, rem_m)."""
        choices = []
        curr_b, curr_m = rem_b, rem_m
        
        for i in range(stage_idx, 0, -1):
            target_score = dp[i][curr_b][curr_m]
            found = False
            
            # Iterate through options in ASCENDING index order for lexicographical tie-breaking
            for opt_idx, opt in enumerate(stages[i]):
                prev_b = curr_b - opt.budget
                prev_m = curr_m - opt.memory
                
                if prev_b >= 0 and prev_m >= 0:
                    if dp[i - 1][prev_b][prev_m] != -1:
                        if dp[i - 1][prev_b][prev_m] + opt.score == target_score:
                            choices.append(opt_idx)
                            curr_b, curr_m = prev_b, prev_m
                            found = True
                            break  # Pick smallest option index that satisfies DP transition
            if not found:
                return None
        
        # Stage 0 choice
        target_score = dp[0][curr_b][curr_m]
        found_stage_0 = False
        for opt_idx, opt in enumerate(stages[0]):
            if opt.budget == curr_b and opt.memory == curr_m and opt.score == target_score:
                choices.append(opt_idx)
                found_stage_0 = True
                break
                
        if not found_stage_0:
            return None
            
        choices.reverse()
        return choices

    # Search across all optimal (budget, memory) endpoints for the lexicographically smallest vector
    best_choices: Optional[List[int]] = None
    best_b, best_m = 0, 0

    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            if dp[N - 1][b][m] == max_score:
                candidate_choices = reconstruct(N - 1, b, m)
                if candidate_choices is not None:
                    if best_choices is None or candidate_choices < best_choices:
                        best_choices = candidate_choices
                        best_b, best_m = b, m

    return max_score, best_b, best_m, best_choices


# Verification on the Minimal Failing Example
if __name__ == "__main__":
    stage_0 = [
        Option(budget=2, memory=2, score=10), # Option 0
        Option(budget=1, memory=1, score=10), # Option 1
    ]
    stage_1 = [
        Option(budget=1, memory=1, score=10), # Option 0
    ]

    result = solve_mckp_2d([stage_0, stage_1], max_budget=10, max_memory=10)
    
    if result:
        score, b_used, m_used, choices = result
        print(f"Optimal Score: {score}")
        print(f"Budget Used: {b_used}, Memory Used: {m_used}")
        print(f"Choices Vector: {choices}") 
        # Output choice vector will correctly be [0, 0] instead of [1, 0]