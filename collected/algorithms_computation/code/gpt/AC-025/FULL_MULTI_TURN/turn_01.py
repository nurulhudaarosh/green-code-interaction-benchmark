"""
Multi-Stage Resource Allocation

Problem:
    There are several stages, and exactly one option must be selected from
    each stage. Every option has:
        - budget consumption
        - memory consumption
        - score

    Choose exactly one option per stage so that the total budget and total
    memory do not exceed their global limits.

    Primary objective:
        Maximize total score.

    Tie-breaking:
        Among all choices with the maximum score, return the
        lexicographically smallest choice vector.

Key constraints:
    - Every stage must contribute exactly one selected option.
    - Total budget <= budget_limit.
    - Total memory <= memory_limit.
    - Scores are maximized.
    - If multiple solutions have the same maximum score, the vector of
      selected option indices must be lexicographically smallest.
    - The solution is deterministic.
    - Standard library only; no network, APIs, external services,
      randomness, or human interaction.

Required output:
    A dictionary containing:
        {
            "max_score": maximum achievable total score,
            "choice_vector": lexicographically smallest optimal vector,
        }

Algorithm:
    Use layered two-resource dynamic programming.

    A DP state after processing some stages is identified by:
        (total_budget, total_memory)

    For every reachable state, store the best score achievable at that
    resource usage. When adding an option from the next stage, update the
    corresponding resource state.

    For deterministic tie handling, when two choices reach the same
    resource state with the same score, keep the lexicographically smaller
    choice prefix.

    After all stages are processed, inspect every feasible final state,
    choose the maximum score, and among equal scores choose the
    lexicographically smallest choice vector.

    Complexity:
        Let S be the number of stages, B the budget limit, M the memory
        limit, and O the maximum number of options in a stage.

        Time:  O(S * B * M * O) in the straightforward bounded-state DP.
        Space: O(B * M) for the current layer plus stored choice prefixes.

    The implementation below keeps complete choice prefixes in each DP
    state. This makes deterministic reconstruction simple and directly
    enforces lexicographic tie-breaking.
"""

from typing import Any, Dict, List, Sequence, Tuple


def multi_stage_resource_allocation(
    stages: Sequence[Sequence[Tuple[int, int, int]]],
    budget_limit: int,
    memory_limit: int,
) -> Dict[str, Any]:
    """
    Solve the Multi-Stage Resource Allocation problem.

    Parameters
    ----------
    stages:
        stages[i] contains the options for stage i.
        Each option is (budget, memory, score).
        Option indices are zero-based and follow their input order.

    budget_limit:
        Maximum total budget allowed.

    memory_limit:
        Maximum total memory allowed.

    Returns
    -------
    dict
        {
            "max_score": int,
            "choice_vector": List[int]
        }

    If no feasible solution exists, returns:
        {
            "max_score": None,
            "choice_vector": []
        }
    """

    if budget_limit < 0 or memory_limit < 0:
        raise ValueError("Resource limits must be non-negative.")

    # Empty stage list:
    # selecting zero options is the only possible choice.
    if not stages:
        return {
            "max_score": 0,
            "choice_vector": [],
        }

    # Validate the input before running the DP.
    for stage_index, options in enumerate(stages):
        if not options:
            # Exactly one option is required from every stage, so an empty
            # stage makes the complete problem infeasible.
            return {
                "max_score": None,
                "choice_vector": [],
            }

        for option_index, option in enumerate(options):
            if len(option) != 3:
                raise ValueError(
                    f"Stage {stage_index}, option {option_index} "
                    "must be (budget, memory, score)."
                )

            budget, memory, score = option

            if budget < 0 or memory < 0:
                raise ValueError(
                    f"Stage {stage_index}, option {option_index} "
                    "has negative resource consumption."
                )

    # State:
    #   (used_budget, used_memory) -> (best_score, choice_prefix)
    #
    # Keeping the complete prefix makes tie-breaking explicit and
    # deterministic.
    dp: Dict[Tuple[int, int], Tuple[int, Tuple[int, ...]]] = {
        (0, 0): (0, ())
    }

    for options in stages:
        next_dp: Dict[Tuple[int, int], Tuple[int, Tuple[int, ...]]] = {}

        for (used_budget, used_memory), (current_score, prefix) in dp.items():
            for option_index, (option_budget, option_memory, option_score) in enumerate(
                options
            ):
                new_budget = used_budget + option_budget
                new_memory = used_memory + option_memory

                if new_budget > budget_limit:
                    continue
                if new_memory > memory_limit:
                    continue

                new_score = current_score + option_score
                new_prefix = prefix + (option_index,)
                state = (new_budget, new_memory)

                old = next_dp.get(state)

                if old is None:
                    next_dp[state] = (new_score, new_prefix)
                else:
                    old_score, old_prefix = old

                    # Primary comparison: higher score.
                    # Tie-break: lexicographically smaller choice vector.
                    if (
                        new_score > old_score
                        or (
                            new_score == old_score
                            and new_prefix < old_prefix
                        )
                    ):
                        next_dp[state] = (new_score, new_prefix)

        dp = next_dp

        # No resource-feasible partial solution remains.
        if not dp:
            return {
                "max_score": None,
                "choice_vector": [],
            }

    # Select the best complete solution among all feasible resource states.
    best_score = None
    best_prefix: Tuple[int, ...] | None = None

    for score, prefix in dp.values():
        if best_score is None or score > best_score:
            best_score = score
            best_prefix = prefix
        elif score == best_score and prefix < best_prefix:
            best_prefix = prefix

    return {
        "max_score": best_score,
        "choice_vector": list(best_prefix),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _run_tests() -> None:
    # 1. Basic feasible case.
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

    # 2. Lexicographic tie-breaking.
    #
    # [0, 1] and [1, 0] both have score 10 and satisfy the limits.
    # [0, 1] is lexicographically smaller.
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

    # 3. Smallest permitted input: one stage, one option.
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

    # 4. Empty stage structure.
    #
    # With no stages, selecting nothing is feasible and has score zero.
    result = multi_stage_resource_allocation(
        [],
        budget_limit=0,
        memory_limit=0,
    )

    assert result == {
        "max_score": 0,
        "choice_vector": [],
    }

    # 5. Empty stage makes the problem infeasible because exactly one
    # option must be selected from every stage.
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

    # 6. No complete solution fits the resource limits.
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

    # 7. Budget and memory both matter.
    stages = [
        [
            (2, 5, 8),
            (5, 2, 9),
        ],
        [
            (2, 5, 8),
            (5, 2, 9),
        ],
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

    # 8. Negative scores are allowed; exactly one option is still required.
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

    # 9. Equal-score and equal-resource alternatives must use the smaller
    # option index.
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

    # 10. A larger valid structure to exercise repeated DP transitions.
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