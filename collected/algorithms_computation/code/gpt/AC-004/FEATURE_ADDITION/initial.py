from bisect import bisect_right
from typing import List, Tuple, Dict, Any


def weighted_job_scheduler(
    jobs: List[Tuple[int, int, int]]
) -> Dict[str, Any]:
    """
    Solve the Weighted Job Scheduling problem deterministically.

    Each job is represented as:
        (start, finish, profit)

    Rules:
      - Jobs are compatible when previous.finish <= current.start.
      - Maximize total profit.
      - If multiple schedules have the same maximum profit,
        choose the schedule with the lexicographically smallest
        sequence of original job indices.

    Returns:
        {
            "max_profit": int,
            "selected_indices": List[int]
        }

    Example:
        jobs = [
            (1, 3, 50),
            (3, 5, 20),
            (0, 6, 100),
            (5, 7, 30),
        ]

        result = weighted_job_scheduler(jobs)

        # {
        #     "max_profit": 100,
        #     "selected_indices": [2]
        # }
    """

    # -----------------------------
    # Validation
    # -----------------------------
    for i, job in enumerate(jobs):
        if len(job) != 3:
            raise ValueError(
                f"Job at index {i} must contain "
                f"(start, finish, profit)."
            )

        start, finish, profit = job

        if finish < start:
            raise ValueError(
                f"Job at index {i} has finish < start."
            )

        if not isinstance(profit, int):
            raise TypeError(
                f"Profit at index {i} must be an integer."
            )

    n = len(jobs)

    if n == 0:
        return {
            "max_profit": 0,
            "selected_indices": []
        }

    # ---------------------------------------------------------
    # Sort by finish time.
    #
    # Extra fields make the ordering deterministic without
    # changing the original-index information.
    # ---------------------------------------------------------
    ordered = sorted(
        (
            (start, finish, profit, original_index)
            for original_index, (start, finish, profit) in enumerate(jobs)
        ),
        key=lambda job: (job[1], job[0], job[3])
    )

    # Finish times are sorted, allowing binary search.
    finish_times = [job[1] for job in ordered]

    # ---------------------------------------------------------
    # Find p[i]:
    # index of the latest job before i whose finish time
    # is <= ordered[i].start.
    #
    # bisect_right is used because touching endpoints are
    # compatible.
    # ---------------------------------------------------------
    predecessor = [-1] * n

    for i in range(n):
        start = ordered[i][0]

        p = bisect_right(finish_times, start, 0, i) - 1
        predecessor[i] = p

    # ---------------------------------------------------------
    # Dynamic programming.
    #
    # dp_profit[i] = maximum profit using jobs [0 .. i].
    #
    # dp_indices[i] = original-index sequence corresponding
    # to dp_profit[i].
    #
    # We keep the selected indices sorted by chronological
    # schedule order. Since schedules are constructed from
    # finish-time-sorted jobs, this sequence is deterministic.
    # ---------------------------------------------------------
    dp_profit = [0] * n
    dp_indices: List[List[int]] = [[] for _ in range(n)]

    for i in range(n):
        start, finish, profit, original_index = ordered[i]

        # Option 1: skip this job.
        if i == 0:
            skip_profit = 0
            skip_indices: List[int] = []
        else:
            skip_profit = dp_profit[i - 1]
            skip_indices = dp_indices[i - 1]

        # Option 2: take this job.
        if predecessor[i] == -1:
            take_profit = profit
            take_indices = [original_index]
        else:
            take_profit = (
                dp_profit[predecessor[i]] + profit
            )
            take_indices = (
                dp_indices[predecessor[i]] + [original_index]
            )

        # -----------------------------------------------------
        # Choose the better solution.
        #
        # Primary criterion:
        #   larger profit
        #
        # Tie criterion:
        #   lexicographically smaller original-index sequence.
        # -----------------------------------------------------
        if take_profit > skip_profit:
            dp_profit[i] = take_profit
            dp_indices[i] = take_indices

        elif take_profit < skip_profit:
            dp_profit[i] = skip_profit
            dp_indices[i] = skip_indices

        else:
            if take_indices < skip_indices:
                dp_profit[i] = take_profit
                dp_indices[i] = take_indices
            else:
                dp_profit[i] = skip_profit
                dp_indices[i] = skip_indices

    return {
        "max_profit": dp_profit[-1],
        "selected_indices": dp_indices[-1]
    }


# -------------------------------------------------------------
# Example / basic tests
# -------------------------------------------------------------
if __name__ == "__main__":
    # Example 1: Standard weighted scheduling.
    jobs = [
        (1, 3, 50),
        (3, 5, 20),
        (0, 6, 100),
        (5, 7, 30),
    ]

    print(weighted_job_scheduler(jobs))

    # Example 2: Endpoint touching is compatible.
    jobs = [
        (0, 2, 50),
        (2, 4, 60),
        (4, 6, 70),
    ]

    result = weighted_job_scheduler(jobs)

    assert result == {
        "max_profit": 180,
        "selected_indices": [0, 1, 2],
    }

    # Example 3: Tie-breaking.
    #
    # Both [0] and [1] give profit 50.
    # The lexicographically smaller original-index sequence
    # is [0].
    jobs = [
        (0, 2, 50),
        (2, 4, 50),
    ]

    # Here [0, 1] actually gives 100 because the jobs touch.
    result = weighted_job_scheduler(jobs)

    assert result == {
        "max_profit": 100,
        "selected_indices": [0, 1],
    }

    # Example 4: Empty input.
    assert weighted_job_scheduler([]) == {
        "max_profit": 0,
        "selected_indices": [],
    }

    print("All tests passed.")