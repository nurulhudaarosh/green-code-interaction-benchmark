"""
Problem: Multi-Stage Resource Allocation

Restatement:
- There are multiple stages.
- From every stage, exactly one option must be selected.
- Each option consumes some budget and memory and provides a score.
- The total budget and total memory must stay within their global limits.
- Maximize the total score.
- If multiple solutions have the same maximum score, return the
  lexicographically smallest choice vector.

Key constraints / requirements:
- Exactly one option must be selected from each stage.
- Every option has:
    budget >= 0
    memory >= 0
    score
- Total budget <= budget_limit.
- Total memory <= memory_limit.
- The choice vector contains one option index per stage.
- Objective:
    1. maximize total score;
    2. among equal-score solutions, choose the lexicographically
       smallest choice vector.
- The implementation must be deterministic.
- Standard library only.
- No network access, APIs, external services, randomness, or
  human interaction.

Required output:
A dictionary containing:
    {
        "max_score": maximum achievable total score,
        "total_budget": budget consumed by the selected options,
        "total_memory": memory consumed by the selected options,
        "choice_vector": lexicographically smallest optimal option indices
    }

If no feasible selection exists, return:
    {
        "max_score": None,
        "total_budget": None,
        "total_memory": None,
        "choice_vector": []
    }

Algorithm:
Use layered two-resource dynamic programming.

For each stage, maintain states indexed by:
    (total_budget, total_memory)

For every reachable state, try every option in the next stage.
For each resulting resource pair, retain the solution with:
    1. larger score;
    2. if scores tie, lexicographically smaller choice vector.

Each stage forms one DP layer, so an option from exactly one stage
is added at every transition.

Deterministic reconstruction:
The DP state stores the complete choice vector for the best solution
reaching that state. Since ties are explicitly resolved using tuple
comparison, the final selection is deterministic and automatically
gives the lexicographically smallest choice vector among all maximum-
score solutions.

Time complexity:
    O(S * B * M * O)
where:
    S = number of stages,
    B = budget limit + 1,
    M = memory limit + 1,
    O = maximum number of options in a stage.

Space complexity:
    O(B * M), apart from the stored choice vectors.

Input representation:
    stages = [
        [
            {"budget": ..., "memory": ..., "score": ...},
            ...
        ],
        ...
    ]

The option index is its zero-based position inside its stage.
"""


def multi_stage_resource_allocation(stages, budget_limit, memory_limit):
    """
    Solve the Multi-Stage Resource Allocation problem.

    Parameters
    ----------
    stages : list[list[dict]]
        Each stage contains option dictionaries with keys:
        "budget", "memory", and "score".

    budget_limit : int
        Maximum total budget.

    memory_limit : int
        Maximum total memory.

    Returns
    -------
    dict
        Required deterministic result.
    """

    # Basic validity checks for the stated problem model.
    if budget_limit < 0 or memory_limit < 0:
        return {
            "max_score": None,
            "total_budget": None,
            "total_memory": None,
            "choice_vector": [],
        }

    if not stages:
        return {
            "max_score": 0,
            "total_budget": 0,
            "total_memory": 0,
            "choice_vector": [],
        }

    # Every stage requires exactly one option.
    # Therefore an empty stage makes the whole instance infeasible.
    if any(not stage for stage in stages):
        return {
            "max_score": None,
            "total_budget": None,
            "total_memory": None,
            "choice_vector": [],
        }

    # dp[(budget, memory)] =
    #     (score, choice_vector)
    #
    # Only the current layer is retained.
    dp = {(0, 0): (0, ())}

    for stage in stages:
        next_dp = {}

        for (used_budget, used_memory), (score, choices) in dp.items():
            for option_index, option in enumerate(stage):
                option_budget = option["budget"]
                option_memory = option["memory"]
                option_score = option["score"]

                new_budget = used_budget + option_budget
                new_memory = used_memory + option_memory

                if new_budget > budget_limit:
                    continue
                if new_memory > memory_limit:
                    continue

                new_score = score + option_score
                new_choices = choices + (option_index,)

                state = (new_budget, new_memory)
                candidate = (new_score, new_choices)

                current = next_dp.get(state)

                if current is None:
                    next_dp[state] = candidate
                else:
                    current_score, current_choices = current

                    # Higher score is better.
                    # For equal scores, lexicographically smaller
                    # choice vector is better.
                    if (
                        new_score > current_score
                        or (
                            new_score == current_score
                            and new_choices < current_choices
                        )
                    ):
                        next_dp[state] = candidate

        # No reachable state means no feasible solution can continue.
        if not next_dp:
            return {
                "max_score": None,
                "total_budget": None,
                "total_memory": None,
                "choice_vector": [],
            }

        dp = next_dp

    # Select the globally best final state.
    #
    # Primary key: maximum score.
    # Secondary key: lexicographically smallest choice vector.
    best_budget = None
    best_memory = None
    best_score = None
    best_choices = None

    for (used_budget, used_memory), (score, choices) in dp.items():
        if best_score is None:
            best_score = score
            best_budget = used_budget
            best_memory = used_memory
            best_choices = choices
            continue

        if score > best_score:
            best_score = score
            best_budget = used_budget
            best_memory = used_memory
            best_choices = choices
        elif score == best_score and choices < best_choices:
            best_budget = used_budget
            best_memory = used_memory
            best_choices = choices

    return {
        "max_score": best_score,
        "total_budget": best_budget,
        "total_memory": best_memory,
        "choice_vector": list(best_choices),
    }


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

if __name__ == "__main__":
    # Test 1:
    # Two stages, two resources, normal feasible case.
    stages = [
        [
            {"budget": 2, "memory": 3, "score": 8},
            {"budget": 1, "memory": 2, "score": 5},
        ],
        [
            {"budget": 3, "memory": 2, "score": 7},
            {"budget": 2, "memory": 4, "score": 6},
        ],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=5,
        memory_limit=5,
    )

    assert result == {
        "max_score": 15,
        "total_budget": 5,
        "total_memory": 5,
        "choice_vector": [0, 0],
    }

    # Test 2:
    # Equal maximum scores. The lexicographically smaller choice
    # vector must be selected.
    stages = [
        [
            {"budget": 1, "memory": 1, "score": 10},
            {"budget": 2, "memory": 1, "score": 10},
        ],
        [
            {"budget": 1, "memory": 1, "score": 5},
            {"budget": 2, "memory": 1, "score": 5},
        ],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=4,
        memory_limit=2,
    )

    assert result == {
        "max_score": 15,
        "total_budget": 2,
        "total_memory": 2,
        "choice_vector": [0, 0],
    }

    # Test 3:
    # A locally better option can be globally worse because of
    # the two resource limits.
    stages = [
        [
            {"budget": 4, "memory": 4, "score": 100},
            {"budget": 1, "memory": 1, "score": 20},
        ],
        [
            {"budget": 1, "memory": 1, "score": 20},
            {"budget": 1, "memory": 1, "score": 20},
        ],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=2,
        memory_limit=2,
    )

    assert result == {
        "max_score": 40,
        "total_budget": 2,
        "total_memory": 2,
        "choice_vector": [1, 0],
    }

    # Test 4:
    # No feasible solution.
    stages = [
        [
            {"budget": 5, "memory": 5, "score": 10},
        ],
        [
            {"budget": 1, "memory": 1, "score": 5},
        ],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=5,
        memory_limit=5,
    )

    assert result == {
        "max_score": None,
        "total_budget": None,
        "total_memory": None,
        "choice_vector": [],
    }

    # Test 5:
    # Empty stage means exactly-one selection is impossible.
    stages = [
        [
            {"budget": 1, "memory": 1, "score": 10},
        ],
        [],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=10,
        memory_limit=10,
    )

    assert result == {
        "max_score": None,
        "total_budget": None,
        "total_memory": None,
        "choice_vector": [],
    }

    # Test 6:
    # Empty set of stages: selecting exactly one option from every
    # stage is vacuously satisfied.
    result = multi_stage_resource_allocation(
        [],
        budget_limit=10,
        memory_limit=10,
    )

    assert result == {
        "max_score": 0,
        "total_budget": 0,
        "total_memory": 0,
        "choice_vector": [],
    }

    print("All tests passed.")