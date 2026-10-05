from typing import List, Tuple, Optional, Union, Dict, Any


def solve_stages(stages: List[List[Tuple[int, int, int]]],
                 budget_limit: int,
                 memory_limit: int,
                 return_operation_summary: bool = False
                 ) -> Union[Tuple[List[int], int],
                            Tuple[List[int], int, Dict[str, int]]]:
    """
    Solve multi-stage resource allocation problem.

    Args:
        stages: List of stages; each stage is a list of (cost, memory, score) tuples.
        budget_limit: Maximum total budget.
        memory_limit: Maximum total memory.
        return_operation_summary: If True, also return a dict with operation counts.
                                  If False (default), behavior is identical to the
                                  original implementation.

    Returns:
        If return_operation_summary is False:
            (choice_vector, max_score)
        If return_operation_summary is True:
            (choice_vector, max_score, operation_summary)

        operation_summary is a dict containing:
            - "dp_decisions":  number of option-fit-and-evaluate decisions during DP fill
            - "reconstruction_decisions": same unit of decision during reconstruction
            - "total_decisions": dp_decisions + reconstruction_decisions
    """
    n_stages = len(stages)

    # Operation counters (only meaningful when feature is requested)
    dp_decisions = 0
    reconstruction_decisions = 0

    if n_stages == 0:
        if return_operation_summary:
            return [], 0, {
                "dp_decisions": 0,
                "reconstruction_decisions": 0,
                "total_decisions": 0,
            }
        return [], 0

    # dp[i][b][m] = max score achievable from stage i..end with remaining (b, m)
    dp = [[[-1] * (memory_limit + 1) for _ in range(budget_limit + 1)]
          for _ in range(n_stages + 1)]

    # Base case: after final stage, score is 0 for any leftover resources
    for b in range(budget_limit + 1):
        for m in range(memory_limit + 1):
            dp[n_stages][b][m] = 0

    # Fill DP table backwards
    for i in range(n_stages - 1, -1, -1):
        stage_options = stages[i]
        for b in range(budget_limit + 1):
            for m in range(memory_limit + 1):
                best_score = -1
                for opt_idx, (cost, mem, score) in enumerate(stage_options):
                    # Each option evaluation at a reachable state counts as a decision
                    dp_decisions += 1
                    if cost <= b and mem <= m:
                        next_score = dp[i + 1][b - cost][m - mem]
                        if next_score != -1:
                            total_score = score + next_score
                            if total_score > best_score:
                                best_score = total_score
                dp[i][b][m] = best_score

    # Feasibility check
    if dp[0][budget_limit][memory_limit] == -1:
        if return_operation_summary:
            return [], -1, {
                "dp_decisions": dp_decisions,
                "reconstruction_decisions": reconstruction_decisions,
                "total_decisions": dp_decisions + reconstruction_decisions,
            }
        return [], -1

    # Deterministic reconstruction (prefer smaller indices on ties)
    choices: List[int] = []
    b, m = budget_limit, memory_limit

    for i in range(n_stages):
        best_opt = -1
        best_score = -1
        for opt_idx, (cost, mem, score) in enumerate(stages[i]):
            reconstruction_decisions += 1
            if cost <= b and mem <= m:
                next_score = dp[i + 1][b - cost][m - mem]
                if next_score != -1:
                    total_score = score + next_score
                    # Strict '>' preserves lexicographically smallest on ties
                    if total_score > best_score:
                        best_score = total_score
                        best_opt = opt_idx

        if best_opt == -1:
            # Should not happen if DP is correct
            if return_operation_summary:
                return [], -1, {
                    "dp_decisions": dp_decisions,
                    "reconstruction_decisions": reconstruction_decisions,
                    "total_decisions": dp_decisions + reconstruction_decisions,
                }
            return [], -1

        choices.append(best_opt)
        cost, mem, _ = stages[i][best_opt]
        b -= cost
        m -= mem

    max_score = dp[0][budget_limit][memory_limit]

    if return_operation_summary:
        return choices, max_score, {
            "dp_decisions": dp_decisions,
            "reconstruction_decisions": reconstruction_decisions,
            "total_decisions": dp_decisions + reconstruction_decisions,
        }

    # Original behavior unchanged when feature disabled
    return choices, max_score


def solve_with_validation(stages: List[List[Tuple[int, int, int]]],
                          budget_limit: int,
                          memory_limit: int,
                          show_operation_summary: bool = False) -> None:
    """
    Solve and print results with validation.

    Original fields (choice_vector, max_score) and their printed form are
    unchanged. When show_operation_summary is True, the operation summary is
    additionally printed.
    """
    print("=" * 60)
    print("Multi-Stage Resource Allocation Solver")
    print("=" * 60)

    print(f"\nStages: {len(stages)}")
    print(f"Budget limit: {budget_limit}")
    print(f"Memory limit: {memory_limit}")

    for i, stage in enumerate(stages):
        print(f"\nStage {i}:")
        for j, (cost, mem, score) in enumerate(stage):
            print(f"  Option {j}: cost={cost}, memory={mem}, score={score}")

    # Call with feature flag
    result = solve_stages(stages, budget_limit, memory_limit,
                          return_operation_summary=show_operation_summary)

    if show_operation_summary:
        choices, max_score, op_summary = result
    else:
        choices, max_score = result
        op_summary = None

    print("\n" + "=" * 60)
    print("SOLUTION")
    print("=" * 60)

    if max_score == -1:
        print("No valid solution exists!")
        if op_summary is not None:
            print("\nOperation Summary:")
            for k, v in op_summary.items():
                print(f"  {k}: {v}")
        return

    total_cost = sum(stages[i][choices[i]][0] for i in range(len(stages)))
    total_mem = sum(stages[i][choices[i]][1] for i in range(len(stages)))
    total_score = sum(stages[i][choices[i]][2] for i in range(len(stages)))

    print(f"\nOptimal choice vector: {choices}")
    print(f"Maximum score: {max_score}")
    print(f"\nResource usage:")
    print(f"  Budget: {total_cost} / {budget_limit}")
    print(f"  Memory: {total_mem} / {memory_limit}")
    print(f"  Score:  {total_score}")

    if op_summary is not None:
        print("\n" + "-" * 40)
        print("OPERATION SUMMARY")
        print("-" * 40)
        print(f"  DP decisions:              {op_summary['dp_decisions']}")
        print(f"  Reconstruction decisions:  {op_summary['reconstruction_decisions']}")
        print(f"  Total decisions:           {op_summary['total_decisions']}")

    print("\n" + "-" * 40)
    print("VALIDATION")
    print("-" * 40)
    assert total_score == max_score, "Score mismatch!"
    assert total_cost <= budget_limit, "Budget exceeded!"
    assert total_mem <= memory_limit, "Memory exceeded!"
    print("✓ All constraints satisfied")


# ------------------------------------------------------------------
# Tests: original behavior + new feature + backward compatibility
# ------------------------------------------------------------------
if __name__ == "__main__":
    stages1 = [
        [(2, 1, 10), (3, 2, 15), (1, 3, 8)],
        [(4, 2, 20), (2, 4, 12), (3, 1, 18)],
        [(2, 2, 14), (1, 1, 7), (4, 3, 25)],
    ]

    # --- Original behavior (feature disabled) ---
    print("\n### FEATURE DISABLED (original behavior) ###")
    result = solve_stages(stages1, 8, 6)
    # Must be a 2-tuple: (choices, max_score)
    assert isinstance(result, tuple) and len(result) == 2, \
        "Feature-disabled path must return exactly (choices, max_score)"
    choices, score = result
    print(f"Result: choices={choices}, max_score={score}")
    assert choices == [1, 0, 2] and score == 53, "Original result changed!"

    # --- Feature enabled ---
    print("\n### FEATURE ENABLED (operation_summary requested) ###")
    choices2, score2, ops = solve_stages(stages1, 8, 6,
                                         return_operation_summary=True)
    assert (choices2, score2) == (choices, score), \
        "Feature must not alter original outputs"
    print(f"Result: choices={choices2}, max_score={score2}")
    print(f"Operation summary: {ops}")
    assert ops["total_decisions"] == ops["dp_decisions"] + ops["reconstruction_decisions"]

    # --- Impossible case with feature enabled ---
    print("\n### IMPOSSIBLE CASE (feature enabled) ###")
    bad_stages = [[(10, 10, 100)], [(10, 10, 100)]]
    c, s, ops2 = solve_stages(bad_stages, 5, 5, return_operation_summary=True)
    print(f"choices={c}, max_score={s}, ops={ops2}")
    assert c == [] and s == -1

    # --- Empty stages ---
    print("\n### EMPTY STAGES ###")
    print("disabled:", solve_stages([], 5, 5))
    print("enabled: ", solve_stages([], 5, 5, return_operation_summary=True))

    # --- Full formatted output for demonstration ---
    print("\n### FULL REPORT (with operation summary) ###")
    solve_with_validation(stages1, 8, 6, show_operation_summary=True)

    print("\nAll assertions passed.")