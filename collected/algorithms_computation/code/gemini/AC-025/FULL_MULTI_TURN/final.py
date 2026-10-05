from typing import List, Tuple, Optional, Dict, Any, Union

class Option:
    def __init__(self, budget: int, memory: int, score: int):
        self.budget = budget
        self.memory = memory
        self.score = score

def solve_mckp_2d(
    stages: List[List[Option]], 
    max_budget: int, 
    max_memory: int,
    include_summary: bool = False
) -> Optional[Union[Tuple[int, int, int, List[int]], Dict[str, Any]]]:
    """
    Solves 2D Multiple-Choice Knapsack Problem using layered 2D dynamic programming
    and deterministic reconstruction with lexicographical tie-breaking.
    
    Handles zero-stage inputs, empty stages (infeasible), zero resource limits,
    and disconnected/unreachable states.
    """
    N = len(stages)

    # Helper function to generate output structure respecting original contract
    def make_response(
        score: int, budget: int, memory: int, choices: List[int],
        dp_ops: int, recon_ops: int
    ):
        if include_summary:
            return {
                "max_score": score,
                "used_budget": budget,
                "used_memory": memory,
                "choices": choices,
                "operation_summary": {
                    "dp_transitions_evaluated": dp_ops,
                    "reconstruction_steps": recon_ops,
                    "total_operations": dp_ops + recon_ops
                }
            }
        return score, budget, memory, choices

    # Edge Case 1: Empty input (0 stages)
    if N == 0:
        return make_response(0, 0, 0, [], 0, 0)

    # Edge Case 2: Disconnected structure (any stage has 0 options)
    if any(len(stage) == 0 for stage in stages):
        return None

    # Track operational performance metrics
    dp_transitions_evaluated = 0
    reconstruction_steps = 0

    # dp[i][b][m] stores max score achievable at stage i with b budget and m memory
    dp = [[[-1] * (max_memory + 1) for _ in range(max_budget + 1)] for _ in range(N)]

    # Stage 0 Initialization
    for opt_idx, opt in enumerate(stages[0]):
        dp_transitions_evaluated += 1
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
                    dp_transitions_evaluated += 1
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
        return None  # Infeasible resource limits

    # Deterministic Reconstruction
    def reconstruct(stage_idx: int, rem_b: int, rem_m: int) -> Tuple[Optional[List[int]], int]:
        local_steps = 0
        choices = []
        curr_b, curr_m = rem_b, rem_m
        
        for i in range(stage_idx, 0, -1):
            target_score = dp[i][curr_b][curr_m]
            found = False
            
            # Search in ASCENDING order of option index for lexicographical priority
            for opt_idx, opt in enumerate(stages[i]):
                local_steps += 1
                prev_b = curr_b - opt.budget
                prev_m = curr_m - opt.memory
                
                if prev_b >= 0 and prev_m >= 0:
                    if dp[i - 1][prev_b][prev_m] != -1:
                        if dp[i - 1][prev_b][prev_m] + opt.score == target_score:
                            choices.append(opt_idx)
                            curr_b, curr_m = prev_b, prev_m
                            found = True
                            break
            if not found:
                return None, local_steps
        
        # Stage 0 choice reconstruction
        target_score = dp[0][curr_b][curr_m]
        found_stage_0 = False
        for opt_idx, opt in enumerate(stages[0]):
            local_steps += 1
            if opt.budget == curr_b and opt.memory == curr_m and opt.score == target_score:
                choices.append(opt_idx)
                found_stage_0 = True
                break
                
        if not found_stage_0:
            return None, local_steps
            
        choices.reverse()
        return choices, local_steps

    # Find lexicographically smallest vector across optimal (budget, memory) endpoints
    best_choices: Optional[List[int]] = None
    best_b, best_m = 0, 0

    for b in range(max_budget + 1):
        for m in range(max_memory + 1):
            if dp[N - 1][b][m] == max_score:
                candidate_choices, steps_taken = reconstruct(N - 1, b, m)
                reconstruction_steps += steps_taken
                if candidate_choices is not None:
                    if best_choices is None or candidate_choices < best_choices:
                        best_choices = candidate_choices
                        best_b, best_m = b, m

    if best_choices is None:
        return None

    return make_response(
        max_score, best_b, best_m, best_choices,
        dp_transitions_evaluated, reconstruction_steps
    )


# Comprehensive Edge Case Test Suite
def run_tests():
    print("Running Edge Case Verification Suite...\n")

    # Test 1: Empty Input (N = 0)
    res_1 = solve_mckp_2d([], max_budget=10, max_memory=10)
    assert res_1 == (0, 0, 0, []), f"Test 1 Failed: {res_1}"
    print("✓ Test 1 Passed: Empty Input (N=0)")

    # Test 2: Disconnected Structure (Stage 1 has 0 options)
    stage_0 = [Option(1, 1, 10)]
    stage_1_empty: List[Option] = []
    res_2 = solve_mckp_2d([stage_0, stage_1_empty], max_budget=10, max_memory=10)
    assert res_2 is None, f"Test 2 Failed: {res_2}"
    print("✓ Test 2 Passed: Disconnected Structure (Empty Stage)")

    # Test 3: Zero Budget and Zero Memory Limits (B_max = 0, M_max = 0)
    stage_zero_cost = [
        Option(0, 0, 5),   # Valid zero cost choice (Option 0)
        Option(1, 0, 10),  # Exceeds budget
    ]
    res_3 = solve_mckp_2d([stage_zero_cost], max_budget=0, max_memory=0)
    assert res_3 == (5, 0, 0, [0]), f"Test 3 Failed: {res_3}"
    print("✓ Test 3 Passed: Limits = (0, 0) with zero-cost option")

    # Test 4: Infeasible Limits
    stage_expensive = [Option(5, 5, 20)]
    res_4 = solve_mckp_2d([stage_expensive], max_budget=2, max_memory=2)
    assert res_4 is None, f"Test 4 Failed: {res_4}"
    print("✓ Test 4 Passed: Infeasible Resource Limits")

    # Test 5: Lexicographical Tie-Breaking Preservation
    # Options 0 and 1 yield identical total score and fit budget/memory
    s0 = [Option(2, 2, 10), Option(1, 1, 10)]
    s1 = [Option(1, 1, 10)]
    res_5 = solve_mckp_2d([s0, s1], max_budget=10, max_memory=10)
    assert res_5 == (20, 3, 3, [0, 0]), f"Test 5 Failed: {res_5}"
    print("✓ Test 5 Passed: Lexicographical Tie-Breaking ([0, 0] over [1, 0])")

    # Test 6: Operation Summary with Feature Flag Enabled
    res_6 = solve_mckp_2d([s0, s1], max_budget=10, max_memory=10, include_summary=True)
    assert isinstance(res_6, dict) and "operation_summary" in res_6
    assert res_6["choices"] == [0, 0]
    print("✓ Test 6 Passed: Operation Summary Feature")

    print("\nAll edge case and behavioral tests passed successfully!")

if __name__ == "__main__":
    run_tests()