from typing import List, Dict, Tuple, Optional

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
    Solves 2D Multiple-Choice Knapsack Problem with lexicographical tie-breaking.
    
    Returns:
        (max_score, used_budget, used_memory, choice_indices) or None if infeasible.
    """
    num_stages = len(stages)
    if num_stages == 0:
        return 0, 0, 0, []

    # dp[b][m] = (max_score, choices_list)
    # Using full choices in state guarantees exact lexicographical tie-breaking across all stages.
    dp: Dict[Tuple[int, int], Tuple[int, List[int]]] = {(0, 0): (0, [])}

    for stage_idx, options in enumerate(stages):
        next_dp: Dict[Tuple[int, int], Tuple[int, List[int]]] = {}

        for opt_idx, opt in enumerate(options):
            b_cost = opt.budget
            m_cost = opt.memory
            score = opt.score

            for (b, m), (prev_score, prev_choices) in dp.items():
                new_b = b + b_cost
                new_m = m + m_cost

                if new_b <= max_budget and new_m <= max_memory:
                    new_score = prev_score + score
                    new_choices = prev_choices + [opt_idx]
                    key = (new_b, new_m)

                    if key not in next_dp:
                        next_dp[key] = (new_score, new_choices)
                    else:
                        existing_score, existing_choices = next_dp[key]
                        if new_score > existing_score:
                            next_dp[key] = (new_score, new_choices)
                        elif new_score == existing_score:
                            # Lexicographical tie-breaking
                            if new_choices < existing_choices:
                                next_dp[key] = (new_score, new_choices)

        dp = next_dp
        if not dp:
            return None  # Infeasible state reached

    # Find global optimal solution considering tie-breaker
    best_score = -1
    best_budget = 0
    best_memory = 0
    best_choices: List[int] = []

    for (b, m), (score, choices) in dp.items():
        if score > best_score:
            best_score = score
            best_budget = b
            best_memory = m
            best_choices = choices
        elif score == best_score:
            if choices < best_choices:
                best_score = score
                best_budget = b
                best_memory = m
                best_choices = choices

    if best_score == -1:
        return None

    return best_score, best_budget, best_memory, best_choices


# Example Usage
if __name__ == "__main__":
    # Stage 0 options
    stage_0 = [
        Option(budget=2, memory=3, score=10),
        Option(budget=1, memory=2, score=10),  # Same score, lower resource cost
    ]
    # Stage 1 options
    stage_1 = [
        Option(budget=3, memory=1, score=15),
        Option(budget=2, memory=4, score=20),
    ]

    budget_limit = 5
    memory_limit = 6

    result = solve_mckp_2d([stage_0, stage_1], budget_limit, memory_limit)
    
    if result:
        max_score, b_used, m_used, choices = result
        print(f"Optimal Score: {max_score}")
        print(f"Budget Used: {b_used}/{budget_limit}")
        print(f"Memory Used: {m_used}/{memory_limit}")
        print(f"Choices Vector (0-indexed): {choices}")
    else:
        print("No feasible selection fits the budget and memory limits.")