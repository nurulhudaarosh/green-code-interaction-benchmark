"""
Multi-Stage Resource Allocation

Original problem
----------------
There are multiple stages. Exactly one option must be selected from every
stage.

Each option is represented as:

    (budget_consumption, memory_consumption, score)

The selected options must satisfy both global resource limits:

    total budget <= budget_limit
    total memory <= memory_limit

The objective is to maximize total score.

If several feasible selections have the same maximum score, the required
tie-breaking rule is to return the lexicographically smallest choice vector.

Original required output
------------------------
When operation_summary is not requested:

    {
        "max_score": maximum achievable score,
        "choice_vector": lexicographically smallest optimal choice vector
    }

If no complete selection is feasible:

    {
        "max_score": None,
        "choice_vector": []
    }

New/previous optional output
----------------------------
If operation_summary=True, preserve both original fields and add:

    "operation_summary": deterministic number of major computational
                         option evaluations performed by the algorithm.

If operation_summary=False, the original output shape remains unchanged.

Difficult valid cases handled explicitly
-----------------------------------------
1. Smallest permitted input:
   - One stage.
   - One option.
   - The only option must be selected if it fits.

2. Empty stage structure:
   - No stages means there is nothing to select.
   - This is treated as a valid empty structure and returns score 0 and
     an empty choice vector.

3. Empty individual stage:
   - Exactly one option is required from every stage.
   - Therefore, an empty individual stage makes the complete problem
     infeasible.

4. Disconnected/resource-isolated DP states:
   - Many budget/memory states may be unreachable.
   - The dictionary-based layered DP stores only reachable states.
   - Such disconnected/unreachable states are safely ignored.

5. Tight resource limits:
   - An option can fit one resource but not the other.
   - Both constraints are enforced independently.

6. Tied optimal solutions:
   - Reconstruction examines options in increasing index order.
   - The first option capable of preserving the globally optimal score is
     selected, guaranteeing the lexicographically smallest vector.

Algorithm
---------
Use layered two-resource dynamic programming.

suffix[i][b, m] stores the maximum score obtainable from stage i onward
with b budget and m memory remaining.

The DP is built backward, one stage at a time.

After obtaining the optimal score, reconstruct the answer from the first
stage. For every stage, examine option indices in increasing order and
select the first option whose score plus the optimal suffix score equals
the required remaining optimal score.

This deterministic reconstruction directly enforces the lexicographic
tie-breaking rule.

Complexity
----------
Let:
    S = number of stages
    B = budget limit
    M = memory limit
    O = maximum options in a stage

Worst-case time:
    O(S * B * M * O)

Worst-case space:
    O(S * B * M)

Only the Python standard library is used.
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

    Each stage requires exactly one selected option.

    Option:
        (budget, memory, score)

    Returns the maximum score and lexicographically smallest optimal
    choice vector. If operation_summary=True, also returns a deterministic
    count of major option evaluations.
    """

    if budget_limit < 0 or memory_limit < 0:
        raise ValueError("Resource limits must be non-negative.")

    operations = 0

    def make_result(
        max_score: Optional[int],
        choice_vector: List[int],
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "max_score": max_score,
            "choice_vector": choice_vector,
        }

        if operation_summary:
            result["operation_summary"] = operations

        return result

    # --------------------------------------------------------------
    # Difficult case 1/2:
    # Empty stage collection.
    #
    # There are no stages, so selecting zero options is the only
    # possible selection and has score zero.
    # --------------------------------------------------------------
    if not stages:
        return make_result(0, [])

    # Validate stages and options.
    for stage_index, options in enumerate(stages):
        # ----------------------------------------------------------
        # Difficult case 3:
        # An empty individual stage is infeasible because exactly
        # one option is required from every stage.
        # ----------------------------------------------------------
        if not options:
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

    # suffix[i][(b, m)] = best score from stage i onward with b budget
    # and m memory remaining.
    suffix: List[Dict[State, int]] = [{} for _ in range(n + 1)]

    # Base layer: no stages remain, so score is zero for every
    # non-negative remaining resource state.
    base: Dict[State, int] = {}

    for remaining_budget in range(budget_limit + 1):
        for remaining_memory in range(memory_limit + 1):
            base[(remaining_budget, remaining_memory)] = 0

    suffix[n] = base

    # --------------------------------------------------------------
    # Layered two-resource DP.
    #
    # Only states that can be reached through a valid option are
    # inserted into each layer. Thus disconnected/unreachable
    # resource states are naturally ignored.
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

                    operations += 1

                    # Both resource limits must hold.
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

    # No complete combination satisfies both global limits.
    if optimal_score is None:
        return make_result(None, [])

    # --------------------------------------------------------------
    # Deterministic reconstruction.
    #
    # Trying indices in ascending order means the first feasible
    # optimal choice is always the lexicographically smallest one.
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
    # ==============================================================
    # 1. Smallest permitted non-empty input.
    #
    # One stage, one option.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[[(1, 1, 7)]],
        budget_limit=1,
        memory_limit=1,
    )

    assert result == {
        "max_score": 7,
        "choice_vector": [0],
    }

    # Same smallest input with operation_summary enabled.
    result = multi_stage_resource_allocation(
        stages=[[(1, 1, 7)]],
        budget_limit=1,
        memory_limit=1,
        operation_summary=True,
    )

    assert result["max_score"] == 7
    assert result["choice_vector"] == [0]
    assert result["operation_summary"] == 2

    # ==============================================================
    # 2. Empty stage structure.
    #
    # No stages means no selections are required.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[],
        budget_limit=0,
        memory_limit=0,
    )

    assert result == {
        "max_score": 0,
        "choice_vector": [],
    }

    result = multi_stage_resource_allocation(
        stages=[],
        budget_limit=10,
        memory_limit=10,
        operation_summary=True,
    )

    assert result == {
        "max_score": 0,
        "choice_vector": [],
        "operation_summary": 0,
    }

    # ==============================================================
    # 3. Empty individual stage.
    #
    # Exactly one option must be selected from every stage, so this
    # structure is infeasible.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(1, 1, 5)],
            [],
            [(1, 1, 5)],
        ],
        budget_limit=10,
        memory_limit=10,
    )

    assert result == {
        "max_score": None,
        "choice_vector": [],
    }

    # ==============================================================
    # 4. Disconnected/unreachable resource states.
    #
    # Only some budget/memory combinations can actually be produced.
    # The DP must ignore unreachable states without affecting the
    # answer.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(5, 5, 10)],
            [(5, 5, 10)],
        ],
        budget_limit=20,
        memory_limit=20,
    )

    assert result == {
        "max_score": 20,
        "choice_vector": [0, 0],
    }

    # ==============================================================
    # 5. Tight budget constraint.
    #
    # Option 1 has the better score but cannot fit the budget.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(2, 1, 5), (4, 1, 100)],
        ],
        budget_limit=2,
        memory_limit=10,
    )

    assert result == {
        "max_score": 5,
        "choice_vector": [0],
    }

    # ==============================================================
    # 6. Tight memory constraint.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(1, 2, 5), (1, 4, 100)],
        ],
        budget_limit=10,
        memory_limit=2,
    )

    assert result == {
        "max_score": 5,
        "choice_vector": [0],
    }

    # ==============================================================
    # 7. No feasible complete solution.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(5, 1, 10)],
            [(1, 5, 10)],
        ],
        budget_limit=5,
        memory_limit=5,
    )

    assert result == {
        "max_score": None,
        "choice_vector": [],
    }

    # ==============================================================
    # 8. Lexicographic tie-breaking.
    #
    # Every combination has score 10. The smallest vector is [0, 0].
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(1, 1, 5), (1, 1, 5)],
            [(1, 1, 5), (1, 1, 5)],
        ],
        budget_limit=2,
        memory_limit=2,
    )

    assert result == {
        "max_score": 10,
        "choice_vector": [0, 0],
    }

    # ==============================================================
    # 9. Tie-breaking with different resource consumption.
    # Both [0,0] and another vector can reach the same optimal score.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(1, 2, 10), (2, 1, 10)],
            [(2, 1, 10), (1, 2, 10)],
        ],
        budget_limit=3,
        memory_limit=3,
    )

    assert result == {
        "max_score": 20,
        "choice_vector": [0, 0],
    }

    # ==============================================================
    # 10. Negative scores.
    #
    # Exactly one option per stage remains mandatory.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(1, 1, -5), (2, 2, -1)],
            [(1, 1, -3), (2, 2, -2)],
        ],
        budget_limit=4,
        memory_limit=4,
    )

    assert result == {
        "max_score": -3,
        "choice_vector": [1, 0],
    }

    # ==============================================================
    # 11. Operation summary remains deterministic.
    # ==============================================================
    stages = [
        [(1, 1, 2), (2, 1, 3)],
        [(1, 2, 4), (2, 1, 5)],
    ]

    result1 = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=3,
        operation_summary=True,
    )

    result2 = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=3,
        operation_summary=True,
    )

    assert result1 == result2
    assert result1["max_score"] == 8
    assert result1["choice_vector"] == [0, 1]
    assert isinstance(result1["operation_summary"], int)
    assert result1["operation_summary"] > 0

    # ==============================================================
    # 12. Larger valid structure with many unreachable combinations.
    # ==============================================================
    result = multi_stage_resource_allocation(
        stages=[
            [(4, 4, 8), (7, 1, 10), (1, 7, 9)],
            [(3, 5, 7), (5, 3, 8), (8, 8, 20)],
            [(2, 2, 4), (6, 1, 9), (1, 6, 8)],
        ],
        budget_limit=12,
        memory_limit=10,
    )

    assert result == {
        "max_score": 27,
        "choice_vector": [1, 1, 2],
    }

    # ==============================================================
    # 13. Operation summary does not change the original fields.
    # ==============================================================
    stages = [
        [(1, 1, 5), (2, 2, 5)],
        [(1, 1, 5), (2, 2, 5)],
    ]

    without_summary = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=3,
    )

    with_summary = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=3,
        operation_summary=True,
    )

    assert without_summary == {
        "max_score": 10,
        "choice_vector": [0, 0],
    }

    assert with_summary["max_score"] == without_summary["max_score"]
    assert with_summary["choice_vector"] == without_summary["choice_vector"]
    assert "operation_summary" in with_summary


if __name__ == "__main__":
    _run_tests()