id="58321"
"""
Multi-Stage Resource Allocation with operation_summary

Original problem
----------------
There are multiple stages. Exactly one option must be selected from every
stage.

Each option is represented as:

    (budget_consumption, memory_consumption, score)

The selected options must satisfy both global limits:

    total budget <= budget_limit
    total memory <= memory_limit

Primary objective:
    Maximize total score.

Tie-breaking:
    If multiple feasible selections have the same maximum score, return the
    lexicographically smallest choice vector.

Original required output
------------------------
Without the optional operation_summary feature, the result remains exactly:

    {
        "max_score": maximum achievable score,
        "choice_vector": lexicographically smallest optimal choice vector
    }

If no feasible complete selection exists:

    {
        "max_score": None,
        "choice_vector": []
    }

For an empty list of stages:

    {
        "max_score": 0,
        "choice_vector": []
    }

If an individual stage has no options, no complete selection exists.

New feature
-----------
When operation_summary=True, return one additional field:

    "operation_summary": <deterministic integer>

This integer counts the number of major computational decisions/operations
performed by the algorithm.

The counted operations are:
    1. Every option transition considered while building the layered
       two-resource suffix DP.
    2. Every option considered during deterministic reconstruction.

Resource-limit checks that immediately reject an option are still counted
as a considered operation because the algorithm made the decision to
evaluate that option.

When operation_summary=False (the default), the original output fields are
returned unchanged.

Algorithm
---------
Use layered two-resource dynamic programming.

The suffix DP stores:

    suffix[i][remaining_budget, remaining_memory]

= maximum score obtainable from stages i onward with those remaining
resources.

After the optimal score is computed, reconstruct the choice vector
deterministically from the first stage onward.

At each stage, options are examined in increasing option-index order. The
first option that can still achieve the optimal remaining score is selected.
Therefore the reconstructed vector is guaranteed to be the lexicographically
smallest optimal vector.

Complexity
----------
Let:
    S = number of stages
    B = budget limit
    M = memory limit
    O = maximum number of options in a stage

Time:
    O(S * B * M * O)

Space:
    O(S * B * M)

The implementation uses only the Python standard library.
No network access, APIs, external services, randomness, or human interaction.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple


Option = Tuple[int, int, int]
State = Tuple[int, int]


def multi_stage_resource_allocation(
    stages: Sequence[Sequence[Option]],
    budget_limit: int,
    memory_limit: int,
    operation_summary: bool = False,
) -> Dict[str, Any]:
    """
    Solve Multi-Stage Resource Allocation.

    Parameters
    ----------
    stages:
        A sequence of stages. Each stage contains options represented as
        (budget, memory, score).

    budget_limit:
        Maximum total budget.

    memory_limit:
        Maximum total memory.

    operation_summary:
        If True, include the deterministic number of major computational
        operations in the returned dictionary.

    Returns
    -------
    dict
        Default:
            {
                "max_score": int | None,
                "choice_vector": list[int]
            }

        With operation_summary=True:
            {
                "max_score": int | None,
                "choice_vector": list[int],
                "operation_summary": int
            }
    """

    if budget_limit < 0 or memory_limit < 0:
        raise ValueError("Resource limits must be non-negative.")

    operations = 0

    def make_result(
        max_score: Optional[int],
        choice_vector: List[int],
    ) -> Dict[str, Any]:
        """
        Preserve the original output exactly unless the optional feature
        was explicitly enabled.
        """
        result: Dict[str, Any] = {
            "max_score": max_score,
            "choice_vector": choice_vector,
        }

        if operation_summary:
            result["operation_summary"] = operations

        return result

    # Empty structure.
    if not stages:
        return make_result(0, [])

    # Validate the input.
    for stage_index, options in enumerate(stages):
        if not options:
            # Exactly one option is required from every stage.
            return make_result(None, [])

        for option_index, option in enumerate(options):
            if len(option) != 3:
                raise ValueError(
                    f"Stage {stage_index}, option {option_index} "
                    "must contain (budget, memory, score)."
                )

            option_budget, option_memory, _ = option

            if option_budget < 0 or option_memory < 0:
                raise ValueError(
                    f"Stage {stage_index}, option {option_index} "
                    "has negative resource consumption."
                )

    n = len(stages)

    # suffix[i][b, m] is the best score obtainable from stage i onward
    # with b budget and m memory remaining.
    suffix: List[Dict[State, int]] = [{} for _ in range(n + 1)]

    # Base layer: no stages remain, so score is zero for every feasible
    # remaining-resource state.
    base: Dict[State, int] = {}

    for remaining_budget in range(budget_limit + 1):
        for remaining_memory in range(memory_limit + 1):
            base[(remaining_budget, remaining_memory)] = 0

    suffix[n] = base

    # --------------------------------------------------------------
    # Layered two-resource suffix DP.
    # --------------------------------------------------------------
    for stage_index in range(n - 1, -1, -1):
        current: Dict[State, int] = {}

        for remaining_budget in range(budget_limit + 1):
            for remaining_memory in range(memory_limit + 1):

                best_score: Optional[int] = None

                for (
                    option_budget,
                    option_memory,
                    option_score,
                ) in stages[stage_index]:

                    # One major computational decision:
                    # evaluate this option for this DP state.
                    operations += 1

                    if option_budget > remaining_budget:
                        continue

                    if option_memory > remaining_memory:
                        continue

                    next_state = (
                        remaining_budget - option_budget,
                        remaining_memory - option_memory,
                    )

                    suffix_score = suffix[stage_index + 1].get(
                        next_state
                    )

                    if suffix_score is None:
                        continue

                    candidate_score = option_score + suffix_score

                    if (
                        best_score is None
                        or candidate_score > best_score
                    ):
                        best_score = candidate_score

                if best_score is not None:
                    current[(remaining_budget, remaining_memory)] = (
                        best_score
                    )

        suffix[stage_index] = current

    optimal_score = suffix[0].get(
        (budget_limit, memory_limit)
    )

    if optimal_score is None:
        return make_result(None, [])

    # --------------------------------------------------------------
    # Deterministic reconstruction.
    #
    # Options are tested in increasing index order. The first option
    # that preserves the optimal score is selected, which guarantees
    # the lexicographically smallest optimal choice vector.
    # --------------------------------------------------------------
    remaining_budget = budget_limit
    remaining_memory = memory_limit
    remaining_score = optimal_score

    choice_vector: List[int] = []

    for stage_index, options in enumerate(stages):
        selected = False

        for option_index, (
            option_budget,
            option_memory,
            option_score,
        ) in enumerate(options):

            # This is another major computational decision.
            operations += 1

            if option_budget > remaining_budget:
                continue

            if option_memory > remaining_memory:
                continue

            next_budget = remaining_budget - option_budget
            next_memory = remaining_memory - option_memory

            suffix_score = suffix[stage_index + 1].get(
                (next_budget, next_memory)
            )

            if suffix_score is None:
                continue

            if option_score + suffix_score == remaining_score:
                choice_vector.append(option_index)

                remaining_budget = next_budget
                remaining_memory = next_memory
                remaining_score = suffix_score

                selected = True
                break

        if not selected:
            raise RuntimeError(
                "Deterministic reconstruction failed."
            )

    return make_result(optimal_score, choice_vector)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def _run_tests() -> None:
    # --------------------------------------------------------------
    # Original behavior: operation_summary is disabled by default.
    # The output contains exactly the original two fields.
    # --------------------------------------------------------------
    stages = [
        [(2, 3, 5), (3, 2, 6)],
        [(2, 2, 4), (4, 1, 7)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=6,
        memory_limit=5,
    )

    assert result == {
        "max_score": 13,
        "choice_vector": [1, 1],
    }

    assert "operation_summary" not in result

    # --------------------------------------------------------------
    # New feature enabled.
    # --------------------------------------------------------------
    result = multi_stage_resource_allocation(
        stages,
        budget_limit=6,
        memory_limit=5,
        operation_summary=True,
    )

    assert result["max_score"] == 13
    assert result["choice_vector"] == [1, 1]
    assert isinstance(result["operation_summary"], int)
    assert result["operation_summary"] > 0

    # Repeated execution must produce exactly the same summary.
    result_again = multi_stage_resource_allocation(
        stages,
        budget_limit=6,
        memory_limit=5,
        operation_summary=True,
    )

    assert result == result_again

    # --------------------------------------------------------------
    # Lexicographic tie-breaking.
    # --------------------------------------------------------------
    stages = [
        [(1, 1, 5), (1, 1, 5)],
        [(1, 1, 5), (1, 1, 5)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=2,
        memory_limit=2,
        operation_summary=True,
    )

    assert result["max_score"] == 10
    assert result["choice_vector"] == [0, 0]
    assert isinstance(result["operation_summary"], int)

    # --------------------------------------------------------------
    # Smallest permitted non-empty input.
    # --------------------------------------------------------------
    stages = [
        [(3, 4, 9)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=4,
        operation_summary=True,
    )

    assert result["max_score"] == 9
    assert result["choice_vector"] == [0]
    assert result["operation_summary"] == 2

    # Explanation of 2:
    #   1 operation during the single DP state/option evaluation
    #   1 operation during reconstruction.

    # --------------------------------------------------------------
    # Empty stages.
    # --------------------------------------------------------------
    result = multi_stage_resource_allocation(
        [],
        budget_limit=0,
        memory_limit=0,
        operation_summary=True,
    )

    assert result == {
        "max_score": 0,
        "choice_vector": [],
        "operation_summary": 0,
    }

    # --------------------------------------------------------------
    # Empty individual stage: infeasible.
    # --------------------------------------------------------------
    stages = [
        [(1, 1, 5)],
        [],
        [(1, 1, 5)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=10,
        memory_limit=10,
        operation_summary=True,
    )

    # No DP computation is performed after detecting the impossible
    # empty stage.
    assert result == {
        "max_score": None,
        "choice_vector": [],
        "operation_summary": 0,
    }

    # --------------------------------------------------------------
    # No feasible complete solution.
    # --------------------------------------------------------------
    stages = [
        [(5, 1, 10)],
        [(1, 5, 10)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=5,
        memory_limit=5,
        operation_summary=True,
    )

    assert result["max_score"] is None
    assert result["choice_vector"] == []
    assert result["operation_summary"] > 0

    # --------------------------------------------------------------
    # Both resource constraints matter.
    # --------------------------------------------------------------
    stages = [
        [(2, 5, 8), (5, 2, 9)],
        [(2, 5, 8), (5, 2, 9)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=7,
        memory_limit=7,
        operation_summary=True,
    )

    assert result["max_score"] == 17
    assert result["choice_vector"] == [0, 1]

    # --------------------------------------------------------------
    # Negative scores: exactly one option per stage remains mandatory.
    # --------------------------------------------------------------
    stages = [
        [(1, 1, -5), (2, 2, -1)],
        [(1, 1, -3), (2, 2, -2)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=4,
        memory_limit=4,
        operation_summary=True,
    )

    assert result["max_score"] == -3
    assert result["choice_vector"] == [1, 0]

    # --------------------------------------------------------------
    # Equal scores and equal resource consumption.
    # --------------------------------------------------------------
    stages = [
        [(1, 1, 5), (1, 1, 5)],
        [(1, 1, 5), (1, 1, 5)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=2,
        memory_limit=2,
        operation_summary=True,
    )

    assert result["max_score"] == 10
    assert result["choice_vector"] == [0, 0]

    # --------------------------------------------------------------
    # Different resource usage but tied optimal score.
    # --------------------------------------------------------------
    stages = [
        [(1, 2, 10), (2, 1, 10)],
        [(2, 1, 10), (1, 2, 10)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=3,
        operation_summary=True,
    )

    assert result["max_score"] == 20
    assert result["choice_vector"] == [0, 0]

    # --------------------------------------------------------------
    # A larger valid structure.
    # --------------------------------------------------------------
    stages = [
        [(1, 1, 2), (2, 1, 3), (1, 2, 4)],
        [(1, 2, 3), (2, 1, 4), (2, 2, 5)],
        [(1, 1, 2), (3, 1, 7), (1, 3, 6)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=5,
        memory_limit=4,
        operation_summary=True,
    )

    assert result["max_score"] == 14
    assert result["choice_vector"] == [1, 0, 2]
    assert result["operation_summary"] > 0


if __name__ == "__main__":
    _run_tests()