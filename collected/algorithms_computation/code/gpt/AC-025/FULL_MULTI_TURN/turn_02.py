"""
Multi-Stage Resource Allocation — Bug Report and Corrected Implementation

Problem restatement
-------------------
There are multiple stages. Exactly one option must be selected from every
stage.

Each option has:
    (budget, memory, score)

The selected options must satisfy:
    total budget <= budget_limit
    total memory <= memory_limit

The objective is:
    1. Maximize total score.
    2. If multiple solutions have the same maximum score, return the
       lexicographically smallest choice vector.

Expected behavior
-----------------
The required result is exactly:

    {
        "max_score": maximum achievable score,
        "choice_vector": lexicographically smallest optimal choice vector
    }

If no complete selection is feasible:

    {
        "max_score": None,
        "choice_vector": []
    }

An empty list of stages is a valid empty structure and returns:

    {
        "max_score": 0,
        "choice_vector": []
    }

An empty individual stage is infeasible because every stage requires
exactly one option.

Required algorithm
------------------
Use layered two-resource dynamic programming.

For each stage, maintain feasible states indexed by:

    (used_budget, used_memory)

Each state stores the best score for that resource usage. The DP is layered:
the next layer is built only from states of the previous layer.

Important correction
--------------------
The earlier implementation kept only one prefix per resource state and
used that prefix for tie-breaking immediately. Although that can be made
correct for the lexicographic objective, it does not provide the requested
deterministic reconstruction structure explicitly. More importantly, a
reconstruction-oriented implementation should separate:

    1. the optimal score for each layered resource state, and
    2. deterministic reconstruction of the lexicographically smallest
       optimal choice vector.

The corrected implementation below first computes optimal suffix scores
using layered two-resource DP, then reconstructs the answer from stage 0
forward. At each stage it tries option indices in increasing order and
chooses the first option that can still achieve the globally optimal score.

This directly enforces the required lexicographic rule rather than relying
on incidental dictionary/update ordering.

Defect demonstration
--------------------
Consider:

    stages = [
        [(1, 1, 5), (1, 1, 5)],
        [(1, 1, 5), (1, 1, 5)]
    ]

Both [0, 0], [0, 1], [1, 0], and [1, 1] have score 10 and use the same
resources.

The required answer is:

    {
        "max_score": 10,
        "choice_vector": [0, 0]
    }

A DP that does not explicitly reconstruct using the lexicographic rule can
return another tied vector depending on how equal states are updated or
iterated. That violates the requirement even though the maximum score is
correct.

The corrected version deterministically tests option 0 before option 1 at
each reconstruction step and therefore returns [0, 0].

Complexity
----------
Let:
    S = number of stages
    B = budget limit
    M = memory limit
    O = maximum number of options in a stage

The suffix DP takes O(S * B * M * O) time and O(S * B * M) space.
Reconstruction takes O(S * O) additional transition checks, with constant
time state lookup for each check.

Only the Python standard library is used.
No network access, APIs, external services, randomness, or human interaction.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple


Option = Tuple[int, int, int]
State = Tuple[int, int]


def multi_stage_resource_allocation(
    stages: Sequence[Sequence[Option]],
    budget_limit: int,
    memory_limit: int,
) -> Dict[str, Any]:
    """
    Return the maximum score and lexicographically smallest optimal
    choice vector.

    Each stage requires exactly one option.

    Option format:
        (budget_consumption, memory_consumption, score)
    """

    if budget_limit < 0 or memory_limit < 0:
        raise ValueError("Resource limits must be non-negative.")

    # Empty collection of stages is a valid empty structure.
    if not stages:
        return {
            "max_score": 0,
            "choice_vector": [],
        }

    # Validate stages and options.
    for stage_index, options in enumerate(stages):
        if not options:
            # Exactly one option is required from every stage.
            return {
                "max_score": None,
                "choice_vector": [],
            }

        for option_index, option in enumerate(options):
            if len(option) != 3:
                raise ValueError(
                    f"Stage {stage_index}, option {option_index} "
                    "must contain (budget, memory, score)."
                )

            budget, memory, _ = option

            if budget < 0 or memory < 0:
                raise ValueError(
                    f"Stage {stage_index}, option {option_index} "
                    "has negative resource consumption."
                )

    n = len(stages)

    # ------------------------------------------------------------------
    # Suffix DP
    #
    # suffix[i][b, m] = maximum score obtainable from stages i..n-1
    #                   when at most b budget and m memory remain.
    #
    # A dictionary is used because many resource states may be unreachable.
    # ------------------------------------------------------------------

    suffix: List[Dict[State, int]] = [{} for _ in range(n + 1)]

    # Base layer: after the last stage, selecting nothing gives score 0
    # whenever the remaining resources are non-negative.
    #
    # We populate all resource capacities so reconstruction can directly
    # query the remaining capacity.
    base: Dict[State, int] = {}

    for b in range(budget_limit + 1):
        for m in range(memory_limit + 1):
            base[(b, m)] = 0

    suffix[n] = base

    NEG_INF = None

    # Build the layers backwards.
    for i in range(n - 1, -1, -1):
        current: Dict[State, int] = {}

        for remaining_budget in range(budget_limit + 1):
            for remaining_memory in range(memory_limit + 1):
                best_score: Optional[int] = NEG_INF

                for option_budget, option_memory, option_score in stages[i]:
                    if (
                        option_budget <= remaining_budget
                        and option_memory <= remaining_memory
                    ):
                        next_state = (
                            remaining_budget - option_budget,
                            remaining_memory - option_memory,
                        )

                        suffix_score = suffix[i + 1].get(next_state)

                        if suffix_score is None:
                            continue

                        candidate = option_score + suffix_score

                        if best_score is None or candidate > best_score:
                            best_score = candidate

                if best_score is not None:
                    current[(remaining_budget, remaining_memory)] = best_score

        suffix[i] = current

    # No option combination can satisfy the global limits.
    optimal_score = suffix[0].get((budget_limit, memory_limit))

    if optimal_score is None:
        return {
            "max_score": None,
            "choice_vector": [],
        }

    # ------------------------------------------------------------------
    # Deterministic reconstruction
    #
    # At every stage:
    #   - try option indices in increasing order;
    #   - select the first option that can still achieve the optimal
    #     remaining score.
    #
    # This explicitly guarantees the lexicographically smallest
    # choice vector among all maximum-score solutions.
    # ------------------------------------------------------------------

    remaining_budget = budget_limit
    remaining_memory = memory_limit
    remaining_score = optimal_score

    choice_vector: List[int] = []

    for i, options in enumerate(stages):
        chosen = False

        for option_index, (
            option_budget,
            option_memory,
            option_score,
        ) in enumerate(options):

            if option_budget > remaining_budget:
                continue

            if option_memory > remaining_memory:
                continue

            next_budget = remaining_budget - option_budget
            next_memory = remaining_memory - option_memory

            suffix_score = suffix[i + 1].get(
                (next_budget, next_memory)
            )

            if suffix_score is None:
                continue

            # The option is part of an optimal solution exactly when
            # its score plus the best possible suffix score equals the
            # remaining optimal score.
            if option_score + suffix_score == remaining_score:
                choice_vector.append(option_index)

                remaining_budget = next_budget
                remaining_memory = next_memory
                remaining_score = suffix_score

                chosen = True
                break

        if not chosen:
            # This should be unreachable if the DP and reconstruction
            # are consistent.
            raise RuntimeError("Deterministic reconstruction failed.")

    return {
        "max_score": optimal_score,
        "choice_vector": choice_vector,
    }


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def _run_tests() -> None:
    # --------------------------------------------------------------
    # Demonstrates the tie-breaking defect.
    #
    # Every combination has the same score and resources.
    # The required lexicographically smallest vector is [0, 0].
    # --------------------------------------------------------------
    stages = [
        [(1, 1, 5), (1, 1, 5)],
        [(1, 1, 5), (1, 1, 5)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=2,
        memory_limit=2,
    )

    assert result == {
        "max_score": 10,
        "choice_vector": [0, 0],
    }

    # --------------------------------------------------------------
    # Basic optimization.
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

    # --------------------------------------------------------------
    # Tie in maximum score; lexicographically smallest vector wins.
    # --------------------------------------------------------------
    stages = [
        [(2, 2, 5), (1, 1, 5)],
        [(1, 1, 5), (2, 2, 5)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=3,
    )

    assert result == {
        "max_score": 10,
        "choice_vector": [0, 1],
    }

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
    )

    assert result == {
        "max_score": 9,
        "choice_vector": [0],
    }

    # --------------------------------------------------------------
    # Empty stage list.
    # --------------------------------------------------------------
    result = multi_stage_resource_allocation(
        [],
        budget_limit=0,
        memory_limit=0,
    )

    assert result == {
        "max_score": 0,
        "choice_vector": [],
    }

    # --------------------------------------------------------------
    # Empty individual stage is infeasible.
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
    )

    assert result == {
        "max_score": None,
        "choice_vector": [],
    }

    # --------------------------------------------------------------
    # No feasible complete selection.
    # --------------------------------------------------------------
    stages = [
        [(5, 1, 10)],
        [(1, 5, 10)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=5,
        memory_limit=5,
    )

    assert result == {
        "max_score": None,
        "choice_vector": [],
    }

    # --------------------------------------------------------------
    # Both resources constrain the answer.
    # --------------------------------------------------------------
    stages = [
        [(2, 5, 8), (5, 2, 9)],
        [(2, 5, 8), (5, 2, 9)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=7,
        memory_limit=7,
    )

    assert result == {
        "max_score": 17,
        "choice_vector": [0, 1],
    }

    # --------------------------------------------------------------
    # Negative scores are allowed. Exactly one option per stage
    # is still mandatory.
    # --------------------------------------------------------------
    stages = [
        [(1, 1, -5), (2, 2, -1)],
        [(1, 1, -3), (2, 2, -2)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=4,
        memory_limit=4,
    )

    assert result == {
        "max_score": -3,
        "choice_vector": [1, 0],
    }

    # --------------------------------------------------------------
    # Equal score but different resource usage.
    # Lexicographic ordering still determines the answer when both
    # are globally optimal.
    # --------------------------------------------------------------
    stages = [
        [(1, 2, 10), (2, 1, 10)],
        [(2, 1, 10), (1, 2, 10)],
    ]

    result = multi_stage_resource_allocation(
        stages,
        budget_limit=3,
        memory_limit=3,
    )

    assert result == {
        "max_score": 20,
        "choice_vector": [0, 0],
    }

    # --------------------------------------------------------------
    # Multiple stages and repeated resource states.
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
    )

    assert result == {
        "max_score": 14,
        "choice_vector": [1, 0, 2],
    }


if __name__ == "__main__":
    _run_tests()