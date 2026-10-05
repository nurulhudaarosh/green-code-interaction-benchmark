"""
Problem Restatement
-------------------
There are multiple stages, and each stage requires choosing exactly one option.

Each option has:
    - a budget cost
    - a memory cost
    - a score

Choose exactly one option from every stage while keeping:
    total budget <= budget_limit
    total memory <= memory_limit

Among all feasible choices, maximize total score. If multiple choices have
the same maximum score, return the lexicographically smallest choice vector.

Key Constraints
---------------
- Exactly one option must be selected from every stage.
- Both total budget and total memory must stay within their global limits.
- Scores are maximized.
- Ties are resolved by the lexicographically smallest vector of option indices.
- The solution must be deterministic.
- Standard library only; no network, APIs, external services, randomness,
  or human interaction.

Required Output
---------------
Return:
    {
        "max_score": maximum achievable total score,
        "choice_vector": lexicographically smallest optimal option-index vector
    }

If no feasible selection exists, return:
    {
        "max_score": None,
        "choice_vector": []
    }

Algorithm
---------
Use layered two-resource dynamic programming.

For each stage, the DP state is:
    (used_budget, used_memory)

For every reachable state, try every option of the current stage and keep
the best score for the resulting resource state.

For deterministic tie handling, each state also stores its choice vector.
When two candidates have the same score, keep the lexicographically smaller
choice vector.

After processing all stages, inspect all feasible final states and select:
    1. the largest score;
    2. among equal scores, the lexicographically smallest choice vector.

This directly performs deterministic reconstruction without requiring a
separate backtracking pass.

Time Complexity
---------------
O(S * B * M * O)

where:
    S = number of stages
    B = budget limit
    M = memory limit
    O = maximum number of options in a stage

Space Complexity
----------------
O(B * M)

for the current layered DP table.

Input Format
------------
stages:
    A list of stages. Each stage is a list of options.

Each option is represented as:
    (budget_cost, memory_cost, score)

budget_limit:
    Maximum allowed total budget.

memory_limit:
    Maximum allowed total memory.

Option indices are zero-based and follow their original order within each
stage.
"""


from typing import List, Tuple, Dict, Any


Option = Tuple[int, int, int]


def maximize_stage_score(
    stages: List[List[Option]],
    budget_limit: int,
    memory_limit: int,
) -> Dict[str, Any]:
    """
    Solve the layered two-resource optimization problem.

    Parameters
    ----------
    stages:
        stages[i] contains the options for stage i.
        Each option is (budget_cost, memory_cost, score).

    budget_limit:
        Maximum total budget.

    memory_limit:
        Maximum total memory.

    Returns
    -------
    dict
        {
            "max_score": int | None,
            "choice_vector": List[int]
        }

    Notes
    -----
    Every stage must have at least one selected option.
    Costs are assumed to be non-negative.
    """

    if budget_limit < 0 or memory_limit < 0:
        raise ValueError("Resource limits must be non-negative.")

    for stage_index, stage in enumerate(stages):
        if not stage:
            raise ValueError(
                f"Stage {stage_index} must contain at least one option."
            )

        for option_index, option in enumerate(stage):
            if len(option) != 3:
                raise ValueError(
                    f"Option {option_index} in stage {stage_index} "
                    "must contain (budget, memory, score)."
                )

            budget, memory, _ = option

            if budget < 0 or memory < 0:
                raise ValueError(
                    "Budget and memory costs must be non-negative."
                )

    # dp[(budget, memory)] = (best_score, lexicographically smallest vector)
    #
    # Initially, no stages have been processed.
    dp: Dict[Tuple[int, int], Tuple[int, Tuple[int, ...]]] = {
        (0, 0): (0, ())
    }

    for stage in stages:
        next_dp: Dict[Tuple[int, int], Tuple[int, Tuple[int, ...]]] = {}

        for (used_budget, used_memory), (current_score, current_vector) in dp.items():

            for option_index, (option_budget, option_memory, option_score) in enumerate(stage):
                new_budget = used_budget + option_budget
                new_memory = used_memory + option_memory

                if new_budget > budget_limit or new_memory > memory_limit:
                    continue

                new_score = current_score + option_score
                new_vector = current_vector + (option_index,)
                state = (new_budget, new_memory)

                existing = next_dp.get(state)

                if existing is None:
                    next_dp[state] = (new_score, new_vector)
                    continue

                existing_score, existing_vector = existing

                if new_score > existing_score:
                    next_dp[state] = (new_score, new_vector)
                elif (
                    new_score == existing_score
                    and new_vector < existing_vector
                ):
                    next_dp[state] = (new_score, new_vector)

        dp = next_dp

        if not dp:
            return {
                "max_score": None,
                "choice_vector": [],
            }

    # Select the best feasible final state.
    best_score = None
    best_vector: Tuple[int, ...] | None = None

    for score, vector in dp.values():
        if best_score is None or score > best_score:
            best_score = score
            best_vector = vector
        elif score == best_score and vector < best_vector:
            best_vector = vector

    if best_score is None:
        return {
            "max_score": None,
            "choice_vector": [],
        }

    return {
        "max_score": best_score,
        "choice_vector": list(best_vector),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _run_tests() -> None:
    # Test 1:
    # Straightforward optimum.
    stages = [
        [(2, 1, 5), (1, 2, 4)],
        [(2, 2, 6), (1, 1, 3)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=4,
        memory_limit=4,
    )

    assert result == {
        "max_score": 11,
        "choice_vector": [0, 0],
    }

    # Test 2:
    # Equal score: lexicographically smallest choice vector wins.
    stages = [
        [(1, 1, 5), (1, 1, 5)],
        [(1, 1, 5), (1, 1, 5)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=2,
        memory_limit=2,
    )

    assert result == {
        "max_score": 10,
        "choice_vector": [0, 0],
    }

    # Test 3:
    # A locally worse choice can enable a better global solution.
    stages = [
        [(4, 4, 10), (2, 2, 7)],
        [(2, 2, 10), (3, 3, 20)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=5,
        memory_limit=5,
    )

    assert result == {
        "max_score": 27,
        "choice_vector": [1, 1],
    }

    # Test 4:
    # No feasible solution.
    stages = [
        [(5, 1, 10)],
        [(1, 5, 10)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=5,
        memory_limit=5,
    )

    assert result == {
        "max_score": None,
        "choice_vector": [],
    }

    # Test 5:
    # Negative scores are allowed; exactly one option per stage is still
    # mandatory.
    stages = [
        [(1, 1, -5), (2, 1, -2)],
        [(1, 1, -3), (1, 2, -1)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=3,
        memory_limit=3,
    )

    assert result == {
        "max_score": -3,
        "choice_vector": [1, 0],
    }

    # Test 6:
    # Zero resource limits with zero-cost options.
    stages = [
        [(0, 0, 3), (1, 0, 10)],
        [(0, 0, 4), (0, 1, 20)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=0,
        memory_limit=0,
    )

    assert result == {
        "max_score": 7,
        "choice_vector": [0, 0],
    }

    # Test 7:
    # Tie at different resource states: final comparison still selects the
    # lexicographically smallest optimal vector.
    stages = [
        [(1, 0, 5), (0, 1, 5)],
        [(0, 1, 5), (1, 0, 5)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=1,
        memory_limit=1,
    )

    assert result == {
        "max_score": 10,
        "choice_vector": [0, 0],
    }

    # Test 8:
    # Multiple stages and several dominated/intermediate states.
    stages = [
        [(2, 1, 4), (1, 3, 5), (3, 2, 6)],
        [(1, 2, 4), (2, 1, 7)],
        [(2, 2, 5), (1, 1, 4)],
    ]

    result = maximize_stage_score(
        stages,
        budget_limit=6,
        memory_limit=6,
    )

    assert result == {
        "max_score": 17,
        "choice_vector": [0, 1, 0],
    }


if __name__ == "__main__":
    _run_tests()
    print("All tests passed.")