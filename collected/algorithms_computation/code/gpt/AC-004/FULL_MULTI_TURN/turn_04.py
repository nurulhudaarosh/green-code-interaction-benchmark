"""
Weighted Job Scheduler
======================

Original Problem
----------------
Given a collection of jobs, where each job is represented as:

    (start, finish, profit)

select a subset of mutually non-overlapping jobs that maximizes total profit.

Compatibility rule:
    If one job finishes at time t and another starts at time t, they are
    compatible.

Therefore:

    previous_finish <= next_start

Tie-breaking rule:
    If multiple schedules have the same maximum profit, return the schedule
    whose sequence of original job indices is lexicographically smallest.

Required output
---------------
By default:

    {
        "max_profit": <maximum total profit>,
        "selected_jobs": [<original indices in scheduling order>]
    }

Optional operation-summary feature
----------------------------------
If:

    include_operation_summary=True

is supplied, an additional deterministic field is returned:

    "operation_summary": {
        "jobs_processed": ...,
        "predecessor_searches": ...,
        "dp_decisions": ...,
        "tie_comparisons": ...,
        "total_major_operations": ...
    }

When the option is not requested, the original output remains unchanged.

Algorithm
---------
1. Sort jobs by finish time.
2. Use binary search to find the latest compatible predecessor for each job.
3. Use dynamic programming to choose between:
       - skipping the current job
       - taking the current job and the best compatible predecessor schedule
4. For equal profits, use the lexicographically smaller original-index
   sequence.

Difficult / worst-case-like cases explicitly covered
-----------------------------------------------------
The tests include:

1. Large input with many jobs:
       - exercises O(n log n) sorting
       - exercises n binary-search predecessor calculations
       - exercises n DP decisions

2. Large chain of compatible jobs:
       - every job can follow the previous one
       - forces the DP to repeatedly consider take/skip choices

3. Large set of heavily overlapping jobs:
       - predecessor searches repeatedly return early compatible positions
       - DP must reject many overlapping alternatives

4. Many equal-profit jobs:
       - exercises deterministic tie handling

5. Large equal-finish-time group:
       - tests deterministic sorting and predecessor handling

6. Boundary-style intervals:
       - jobs touching exactly at endpoints

The tests verify correctness without changing the required output or
tie-breaking behavior.

Only Python's standard library is used.
No network access, APIs, external services, randomness, or human interaction.
"""

from bisect import bisect_right
from typing import Dict, List, Sequence, Tuple


Job = Tuple[int, int, int]


def weighted_job_scheduler(
    jobs: Sequence[Job],
    include_operation_summary: bool = False,
) -> Dict[str, object]:
    """
    Return the maximum-profit non-overlapping job schedule.

    Parameters
    ----------
    jobs:
        Sequence of (start, finish, profit).

    include_operation_summary:
        If False, return the original two-field result.

        If True, add the deterministic operation_summary field.

    Returns
    -------
    dict
        {
            "max_profit": int,
            "selected_jobs": List[int]
        }

    or, when include_operation_summary=True:

        {
            "max_profit": int,
            "selected_jobs": List[int],
            "operation_summary": {
                ...
            }
        }
    """

    # ---------------------------------------------------------------
    # Deterministic operation counters.
    # ---------------------------------------------------------------
    jobs_processed = 0
    predecessor_searches = 0
    dp_decisions = 0
    tie_comparisons = 0

    n = len(jobs)

    # ---------------------------------------------------------------
    # Empty input.
    # ---------------------------------------------------------------
    if n == 0:
        result = {
            "max_profit": 0,
            "selected_jobs": [],
        }

        if include_operation_summary:
            result["operation_summary"] = {
                "jobs_processed": 0,
                "predecessor_searches": 0,
                "dp_decisions": 0,
                "tie_comparisons": 0,
                "total_major_operations": 0,
            }

        return result

    # ---------------------------------------------------------------
    # Validate jobs and preserve original indices.
    # ---------------------------------------------------------------
    indexed_jobs = []

    for original_index, job in enumerate(jobs):
        if not isinstance(job, (tuple, list)) or len(job) != 3:
            raise ValueError(
                f"Job at index {original_index} must be "
                f"(start, finish, profit)."
            )

        start, finish, profit = job

        if not isinstance(start, int):
            raise TypeError(
                f"Start time of job {original_index} must be an integer."
            )

        if not isinstance(finish, int):
            raise TypeError(
                f"Finish time of job {original_index} must be an integer."
            )

        if not isinstance(profit, int):
            raise TypeError(
                f"Profit of job {original_index} must be an integer."
            )

        if start > finish:
            raise ValueError(
                f"Job at index {original_index} has start time greater "
                f"than finish time."
            )

        indexed_jobs.append(
            (start, finish, profit, original_index)
        )

    # ---------------------------------------------------------------
    # Sort by finish time.
    #
    # The extra keys make equal-finish ordering deterministic.
    # ---------------------------------------------------------------
    indexed_jobs.sort(
        key=lambda job: (job[1], job[0], job[2], job[3])
    )

    finish_times = [job[1] for job in indexed_jobs]

    # ---------------------------------------------------------------
    # Binary-search compatible predecessors.
    #
    # For each job i, find the largest j < i satisfying:
    #
    #     finish[j] <= start[i]
    #
    # bisect_right is important because endpoint-touching jobs are
    # explicitly compatible.
    # ---------------------------------------------------------------
    predecessor: List[int] = [0] * n

    for i, (start, _, _, _) in enumerate(indexed_jobs):
        jobs_processed += 1
        predecessor_searches += 1

        predecessor[i] = (
            bisect_right(finish_times, start, 0, i) - 1
        )

    # ---------------------------------------------------------------
    # Dynamic programming.
    #
    # dp_profit[i] is the maximum profit obtainable from the first
    # i jobs in finish-time order.
    #
    # dp_sequence[i] is the lexicographically smallest original-index
    # sequence achieving that profit.
    #
    # The sequence is kept in scheduling order. It is NOT independently
    # sorted by original index.
    # ---------------------------------------------------------------
    dp_profit: List[int] = [0] * (n + 1)
    dp_sequence: List[Tuple[int, ...]] = [()] * (n + 1)

    for i in range(1, n + 1):
        dp_decisions += 1

        _, _, profit, original_index = indexed_jobs[i - 1]

        # -----------------------------------------------------------
        # Option 1: skip current job.
        # -----------------------------------------------------------
        skip_profit = dp_profit[i - 1]
        skip_sequence = dp_sequence[i - 1]

        # -----------------------------------------------------------
        # Option 2: take current job.
        # -----------------------------------------------------------
        p = predecessor[i - 1]

        take_profit = dp_profit[p + 1] + profit
        take_sequence = dp_sequence[p + 1] + (original_index,)

        # -----------------------------------------------------------
        # Choose maximum profit.
        # -----------------------------------------------------------
        if take_profit > skip_profit:
            dp_profit[i] = take_profit
            dp_sequence[i] = take_sequence

        elif take_profit < skip_profit:
            dp_profit[i] = skip_profit
            dp_sequence[i] = skip_sequence

        else:
            # Equal profit: deterministic lexicographic tie-break.
            tie_comparisons += 1

            if take_sequence < skip_sequence:
                dp_profit[i] = take_profit
                dp_sequence[i] = take_sequence
            else:
                dp_profit[i] = skip_profit
                dp_sequence[i] = skip_sequence

    # ---------------------------------------------------------------
    # Preserve original required output fields.
    # ---------------------------------------------------------------
    result: Dict[str, object] = {
        "max_profit": dp_profit[n],
        "selected_jobs": list(dp_sequence[n]),
    }

    # ---------------------------------------------------------------
    # Optional operation summary.
    # ---------------------------------------------------------------
    if include_operation_summary:
        total_major_operations = (
            jobs_processed
            + predecessor_searches
            + dp_decisions
            + tie_comparisons
        )

        result["operation_summary"] = {
            "jobs_processed": jobs_processed,
            "predecessor_searches": predecessor_searches,
            "dp_decisions": dp_decisions,
            "tie_comparisons": tie_comparisons,
            "total_major_operations": total_major_operations,
        }

    return result


# =====================================================================
# TESTS
# =====================================================================

def _run_tests() -> None:
    """
    Deterministic test suite.

    The final tests deliberately contain large, worst-case-like structures
    to exercise sorting, binary-search predecessor computation, and the
    dynamic-programming loop at scale.
    """

    # ---------------------------------------------------------------
    # Test 1: Empty input.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([]) == {
        "max_profit": 0,
        "selected_jobs": [],
    }

    # ---------------------------------------------------------------
    # Test 2: Single job.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([
        (1, 3, 10),
    ]) == {
        "max_profit": 10,
        "selected_jobs": [0],
    }

    # ---------------------------------------------------------------
    # Test 3: Endpoint touching.
    #
    # [1, 3] and [3, 5] are compatible.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([
        (1, 3, 10),
        (3, 5, 20),
    ]) == {
        "max_profit": 30,
        "selected_jobs": [0, 1],
    }

    # ---------------------------------------------------------------
    # Test 4: Standard weighted scheduling example.
    # ---------------------------------------------------------------
    jobs = [
        (1, 3, 50),   # 0
        (2, 5, 20),   # 1
        (3, 6, 70),   # 2
        (6, 8, 60),   # 3
        (5, 7, 30),   # 4
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 130,
        "selected_jobs": [0, 2],
    }

    # ---------------------------------------------------------------
    # Test 5: Deterministic single-job tie.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([
        (1, 3, 10),   # 0
        (1, 3, 10),   # 1
    ]) == {
        "max_profit": 10,
        "selected_jobs": [0],
    }

    # ---------------------------------------------------------------
    # Test 6: Multi-job tie.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([
        (1, 2, 5),    # 0
        (2, 3, 5),    # 1
        (1, 2, 5),    # 2
        (2, 3, 5),    # 3
    ]) == {
        "max_profit": 10,
        "selected_jobs": [0, 1],
    }

    # ---------------------------------------------------------------
    # Test 7: Original-index order differs from finish-time order.
    #
    # The selected sequence must represent scheduling order.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([
        (3, 4, 5),    # 0
        (1, 2, 5),    # 1
    ]) == {
        "max_profit": 5,
        "selected_jobs": [0],
    }

    # ---------------------------------------------------------------
    # Test 8: Negative profits.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([
        (1, 2, -10),
        (2, 3, -20),
    ]) == {
        "max_profit": 0,
        "selected_jobs": [],
    }

    # ---------------------------------------------------------------
    # Test 9: Zero-profit jobs.
    # ---------------------------------------------------------------
    assert weighted_job_scheduler([
        (1, 2, 0),
        (2, 3, 0),
    ]) == {
        "max_profit": 0,
        "selected_jobs": [],
    }

    # ---------------------------------------------------------------
    # Test 10: Optional operation summary.
    # ---------------------------------------------------------------
    summary_result = weighted_job_scheduler(
        jobs,
        include_operation_summary=True,
    )

    assert summary_result["max_profit"] == 130
    assert summary_result["selected_jobs"] == [0, 2]

    summary = summary_result["operation_summary"]

    assert summary["jobs_processed"] == 5
    assert summary["predecessor_searches"] == 5
    assert summary["dp_decisions"] == 5

    assert summary["total_major_operations"] == (
        summary["jobs_processed"]
        + summary["predecessor_searches"]
        + summary["dp_decisions"]
        + summary["tie_comparisons"]
    )

    # ---------------------------------------------------------------
    # Test 11: Verify operation summary is deterministic.
    # ---------------------------------------------------------------
    result_a = weighted_job_scheduler(
        jobs,
        include_operation_summary=True,
    )

    result_b = weighted_job_scheduler(
        jobs,
        include_operation_summary=True,
    )

    assert result_a == result_b

    # ---------------------------------------------------------------
    # Test 12: Large compatible chain.
    #
    # Worst-case-like structure:
    # - 20,000 jobs
    # - every job can touch the next job
    # - requires n predecessor binary searches
    # - requires n DP decisions
    #
    # Every job has profit 1, so all jobs should be selected.
    # ---------------------------------------------------------------
    n = 20_000

    large_chain = [
        (i, i + 1, 1)
        for i in range(n)
    ]

    chain_result = weighted_job_scheduler(
        large_chain,
        include_operation_summary=True,
    )

    assert chain_result["max_profit"] == n
    assert chain_result["selected_jobs"] == list(range(n))

    chain_summary = chain_result["operation_summary"]

    assert chain_summary["jobs_processed"] == n
    assert chain_summary["predecessor_searches"] == n
    assert chain_summary["dp_decisions"] == n

    # ---------------------------------------------------------------
    # Test 13: Large overlapping structure.
    #
    # 20,000 jobs all overlap heavily.
    # Only one job can be selected.
    #
    # The highest-profit job is the last one, whose profit is n.
    # ---------------------------------------------------------------
    overlapping_jobs = [
        (0, n, i + 1)
        for i in range(n)
    ]

    overlapping_result = weighted_job_scheduler(
        overlapping_jobs,
        include_operation_summary=True,
    )

    assert overlapping_result["max_profit"] == n
    assert overlapping_result["selected_jobs"] == [n - 1]

    overlapping_summary = overlapping_result["operation_summary"]

    assert overlapping_summary["jobs_processed"] == n
    assert overlapping_summary["predecessor_searches"] == n
    assert overlapping_summary["dp_decisions"] == n

    # ---------------------------------------------------------------
    # Test 14: Large equal-profit tie structure.
    #
    # Every job is individually optimal with profit 1.
    # They overlap, so exactly one job can be selected.
    #
    # The lexicographically smallest original-index sequence is [0].
    # ---------------------------------------------------------------
    tie_count = 5_000

    equal_profit_jobs = [
        (0, 10, 1)
        for _ in range(tie_count)
    ]

    tie_result = weighted_job_scheduler(
        equal_profit_jobs,
        include_operation_summary=True,
    )

    assert tie_result["max_profit"] == 1
    assert tie_result["selected_jobs"] == [0]

    tie_summary = tie_result["operation_summary"]

    assert tie_summary["jobs_processed"] == tie_count
    assert tie_summary["predecessor_searches"] == tie_count
    assert tie_summary["dp_decisions"] == tie_count
    assert tie_summary["tie_comparisons"] > 0

    # ---------------------------------------------------------------
    # Test 15: Large group with identical finish times.
    #
    # This checks deterministic sorting and predecessor handling when
    # many jobs share the same finish time.
    # ---------------------------------------------------------------
    same_finish_count = 10_000

    same_finish_jobs = [
        (i, same_finish_count, i + 1)
        for i in range(same_finish_count)
    ]

    same_finish_result = weighted_job_scheduler(
        same_finish_jobs,
        include_operation_summary=True,
    )

    assert same_finish_result["max_profit"] == same_finish_count
    assert same_finish_result["selected_jobs"] == [
        same_finish_count - 1
    ]

    # Only one of these jobs can be selected because all have the same
    # finish time and all start before that finish time.
    assert len(same_finish_result["selected_jobs"]) == 1

    same_finish_summary = same_finish_result["operation_summary"]

    assert same_finish_summary["jobs_processed"] == same_finish_count
    assert same_finish_summary["predecessor_searches"] == same_finish_count
    assert same_finish_summary["dp_decisions"] == same_finish_count

    # ---------------------------------------------------------------
    # Test 16: Boundary-style endpoint chain.
    #
    # All intervals touch exactly at endpoints.
    # ---------------------------------------------------------------
    boundary_jobs = [
        (0, 1, 10),
        (1, 2, 20),
        (2, 3, 30),
        (3, 4, 40),
        (4, 5, 50),
    ]

    assert weighted_job_scheduler(boundary_jobs) == {
        "max_profit": 150,
        "selected_jobs": [0, 1, 2, 3, 4],
    }

    # ---------------------------------------------------------------
    # Test 17: Invalid interval.
    # ---------------------------------------------------------------
    try:
        weighted_job_scheduler([
            (5, 2, 10),
        ])
        raise AssertionError("Expected ValueError.")
    except ValueError:
        pass

    # ---------------------------------------------------------------
    # Test 18: Invalid job shape.
    # ---------------------------------------------------------------
    try:
        weighted_job_scheduler([
            (1, 2),
        ])
        raise AssertionError("Expected ValueError.")
    except ValueError:
        pass

    # ---------------------------------------------------------------
    # Test 19: Invalid start type.
    # ---------------------------------------------------------------
    try:
        weighted_job_scheduler([
            ("1", 2, 10),
        ])
        raise AssertionError("Expected TypeError.")
    except TypeError:
        pass

    # ---------------------------------------------------------------
    # Test 20: Invalid profit type.
    # ---------------------------------------------------------------
    try:
        weighted_job_scheduler([
            (1, 2, 10.5),
        ])
        raise AssertionError("Expected TypeError.")
    except TypeError:
        pass

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()