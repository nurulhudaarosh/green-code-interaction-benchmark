"""
Weighted Job Scheduler
=======================

ORIGINAL PROBLEM (restated)
----------------------------
We are given n jobs, each with a start time, a finish time, and a profit.
We must select a subset of jobs such that:
    - No two selected jobs overlap in time. Jobs that merely touch at
      endpoints (one job's finish time equals another job's start time)
      ARE considered compatible / non-overlapping.
    - The total profit of the selected subset is maximized.

Among all subsets achieving the maximum profit, ties are broken
deterministically by preferring the lexicographically smallest sorted
sequence of original job indices.

KEY CONSTRAINTS
----------------
1. Non-overlap: for two selected jobs i, j (i != j), it must hold that
   job_i.finish <= job_j.start OR job_j.finish <= job_i.start.
2. Touching endpoints are allowed (finish == start is compatible).
3. Determinism: given the same input, the algorithm must always produce
   the same output — no randomness, no reliance on unstable sort or
   unordered structures.
4. Tie-breaking: if multiple subsets achieve the same maximum profit,
   return the one that is lexicographically smallest with respect to
   the sorted list of original indices.

ORIGINAL REQUIRED OUTPUTS (unchanged, always present)
------------------------------------------------------
- The maximum achievable total profit.
- The list of original indices (0-based) of the selected jobs, sorted
  in increasing order, representing the lexicographically smallest
  optimal solution.

NEW FEATURE (opt-in, additive only)
-------------------------------------
When explicitly requested (via `include_summary=True`), the solver
additionally returns an `operation_summary` field: a deterministic
report of the major computational decisions/operations the algorithm
performed while solving the instance. This includes:
    - num_jobs: number of jobs in the input.
    - num_binary_searches: number of binary searches performed to find
      compatible predecessors (one per job).
    - num_dp_decisions: number of dynamic-programming take-vs-skip
      decisions made (one per job, in finish-time order).
    - num_ties_broken: number of times a profit tie between "take" and
      "skip" was resolved via lexicographic index-list comparison.
    - total_major_operations: sum of the binary searches and DP
      decisions above (the two dominant O(n) phases of the algorithm).

This is purely additive: when the feature is disabled (the default,
`include_summary=False`) or simply not requested, the function's
return value, type, and all original fields/behavior are completely
unchanged from the original solver — no `operation_summary` field is
produced or referenced in that path.

ALGORITHM
---------
Classic "Weighted Interval Scheduling" via dynamic programming:

1. Sort jobs by finish time (ascending). Ties in finish time are broken
   by original index to keep the sort deterministic.
2. For each job i (in finish-time order), binary search for the
   rightmost job p(i) whose finish time is <= job i's start time
   (the latest compatible predecessor).
3. Define dp[i] = maximum profit using jobs among the first i (in
   sorted order). Recurrence:
       dp[i] = max(dp[i-1], profit[i] + dp[p(i)+1])
   i.e., either skip job i, or take it and add the best solution among
   its compatible predecessors.
4. To guarantee the lexicographically smallest optimal index set on
   ties, the choice at each step compares not just profit but also the
   resulting candidate index-list, preferring the smaller one on ties.
5. Backtrack through the dp table to reconstruct the chosen jobs, then
   map back to original indices and sort them.

Complexity: O(n log n) for sorting and binary search, O(n) for DP and
reconstruction — overall O(n log n).
"""

from bisect import bisect_right
from dataclasses import dataclass
from typing import List, Tuple, Union, Dict, Any


@dataclass(frozen=True)
class Job:
    index: int    # original index
    start: int
    finish: int
    profit: int


def _find_last_compatible(sorted_jobs: List[Job], i: int) -> int:
    """
    Binary search for the rightmost index j (0-based, j < i) in
    sorted_jobs such that sorted_jobs[j].finish <= sorted_jobs[i].start.
    Returns -1 if no such job exists.

    sorted_jobs is sorted by finish time ascending, so we can binary
    search on the finish times.
    """
    finishes = [job.finish for job in sorted_jobs]
    target = sorted_jobs[i].start
    # bisect_right gives the insertion point after all entries <= target
    pos = bisect_right(finishes, target, 0, i)
    return pos - 1


def schedule_jobs(
    jobs: List[Tuple[int, int, int]],
    include_summary: bool = False,
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, Any]]]:
    """
    Solve the weighted job scheduling problem.

    Parameters
    ----------
    jobs : list of (start, finish, profit) tuples, in original order.
           Original index of jobs[k] is k.
    include_summary : bool, default False.
           When False (default), behavior is IDENTICAL to the original
           solver: returns (max_profit, selected_original_indices).
           When True, additionally computes and returns a deterministic
           `operation_summary` dict as a third tuple element:
           (max_profit, selected_original_indices, operation_summary).

    Returns
    -------
    If include_summary is False:
        (max_profit, selected_original_indices)
    If include_summary is True:
        (max_profit, selected_original_indices, operation_summary)

        max_profit: int, the maximum total profit achievable.
        selected_original_indices: sorted list of original indices of
            the chosen jobs (lexicographically smallest among all
            optimal subsets).
        operation_summary: dict with keys:
            - "num_jobs"
            - "num_binary_searches"
            - "num_dp_decisions"
            - "num_ties_broken"
            - "total_major_operations"
    """
    n = len(jobs)
    if n == 0:
        if include_summary:
            summary = {
                "num_jobs": 0,
                "num_binary_searches": 0,
                "num_dp_decisions": 0,
                "num_ties_broken": 0,
                "total_major_operations": 0,
            }
            return 0, [], summary
        return 0, []

    # Step 1: build Job objects and sort deterministically by
    # (finish, original index) to break ties in finish time.
    job_objs = [
        Job(index=i, start=s, finish=f, profit=p)
        for i, (s, f, p) in enumerate(jobs)
    ]
    sorted_jobs = sorted(job_objs, key=lambda j: (j.finish, j.index))
    m = len(sorted_jobs)

    # Step 2: precompute the last compatible predecessor for each job.
    pred = [_find_last_compatible(sorted_jobs, i) for i in range(m)]
    num_binary_searches = m  # one binary search per job

    # Step 3: DP over sorted jobs.
    # dp[i] = max profit achievable using sorted_jobs[0..i-1] (prefix of size i).
    # choice_indices[i] = sorted list of original indices achieving dp[i],
    #                      chosen to be lexicographically smallest on ties.
    dp = [0] * (m + 1)
    choice_indices: List[List[int]] = [[] for _ in range(m + 1)]

    num_dp_decisions = 0
    num_ties_broken = 0

    for i in range(1, m + 1):
        job = sorted_jobs[i - 1]
        p = pred[i - 1]  # index into sorted_jobs, 0-based; -1 means none

        # Option A: skip this job
        skip_profit = dp[i - 1]
        skip_indices = choice_indices[i - 1]

        # Option B: take this job
        take_profit = job.profit + dp[p + 1]
        take_indices = sorted(choice_indices[p + 1] + [job.index])

        num_dp_decisions += 1  # one take-vs-skip decision per job

        if take_profit > skip_profit:
            dp[i] = take_profit
            choice_indices[i] = take_indices
        elif take_profit < skip_profit:
            dp[i] = skip_profit
            choice_indices[i] = skip_indices
        else:
            # Tie in profit: pick lexicographically smallest index list.
            num_ties_broken += 1
            dp[i] = skip_profit
            choice_indices[i] = min(skip_indices, take_indices)

    max_profit = dp[m]
    selected = sorted(choice_indices[m])

    if not include_summary:
        return max_profit, selected

    total_major_operations = num_binary_searches + num_dp_decisions
    operation_summary = {
        "num_jobs": n,
        "num_binary_searches": num_binary_searches,
        "num_dp_decisions": num_dp_decisions,
        "num_ties_broken": num_ties_broken,
        "total_major_operations": total_major_operations,
    }

    return max_profit, selected, operation_summary


def _demo() -> None:
    """
    Deterministic self-contained demonstration (no I/O, no randomness).
    jobs are given as (start, finish, profit) with original index
    implied by position in the list.
    """
    jobs = [
        (1, 3, 50),   # index 0
        (3, 5, 20),   # index 1  (touches job 0 at t=3 -> compatible)
        (0, 6, 100),  # index 2  (overlaps both 0 and 1)
        (5, 7, 30),   # index 3  (touches job 1 at t=5 -> compatible)
        (6, 9, 40),   # index 4  (touches job 2 and job 3's neighbor)
        (8, 9, 10),   # index 5
    ]

    print("Jobs (index: start, finish, profit):")
    for idx, (s, f, p) in enumerate(jobs):
        print(f"  {idx}: start={s}, finish={f}, profit={p}")

    # --- Original behavior (feature disabled / not requested) ---
    max_profit, selected = schedule_jobs(jobs)
    print("\n[Default call, include_summary=False -> original behavior]")
    print(f"Maximum profit: {max_profit}")
    print(f"Selected original indices: {selected}")

    # --- New feature requested explicitly ---
    max_profit2, selected2, summary = schedule_jobs(jobs, include_summary=True)
    print("\n[include_summary=True -> adds operation_summary]")
    print(f"Maximum profit: {max_profit2}")
    print(f"Selected original indices: {selected2}")
    print(f"Operation summary: {summary}")

    assert (max_profit, selected) == (max_profit2, selected2), (
        "Enabling the summary must not change the core result."
    )


if __name__ == "__main__":
    _demo()