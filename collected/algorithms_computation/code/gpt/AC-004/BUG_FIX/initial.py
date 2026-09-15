"""
Weighted Interval Scheduling
----------------------------

Problem:
Given a collection of jobs, where each job has:
    - start time
    - finish time
    - profit
    - original input index

Select a subset of non-overlapping jobs with maximum total profit.

Compatibility rule:
A job ending at time T is compatible with another job starting at time T.
Therefore, for jobs A and B:
    A.finish <= B.start
is allowed.

Tie-breaking:
If multiple schedules have the same maximum profit, choose the schedule whose
sequence of original job indices is lexicographically smallest.

Algorithm:
1. Sort jobs by (finish time, start time, original index).
2. For each job, use binary search to find the latest earlier job whose
   finish time is <= the current job's start time.
3. Use dynamic programming:
       dp[i] = best schedule using the first i sorted jobs.
   At each job, compare:
       - excluding the job
       - including the job
4. For equal profits, compare the corresponding original-index sequences
   lexicographically.
5. Return the maximum profit and selected original indices.

Complexity:
- Sorting: O(n log n)
- Binary searches: O(n log n)
- Dynamic programming: O(n)
  (Sequence comparisons can add overhead in the worst case because the
   selected-index sequences are explicitly stored.)
- Space: O(n)

The implementation uses only Python's standard library and is deterministic.
"""


from bisect import bisect_right
from typing import Iterable, List, Sequence, Tuple


Job = Tuple[int, int, int]  # (start, finish, profit)


def weighted_interval_scheduling(
    jobs: Sequence[Job],
) -> Tuple[int, List[int]]:
    """
    Solve the weighted interval scheduling problem.

    Parameters
    ----------
    jobs:
        A sequence of (start, finish, profit) tuples.
        The original index of each job is its position in this sequence.

    Returns
    -------
    (maximum_profit, selected_indices)
        maximum_profit:
            Maximum achievable total profit.

        selected_indices:
            Original indices of the selected jobs, sorted by the jobs'
            chronological finish order. If several schedules have the same
            profit, the lexicographically smallest original-index sequence
            is returned.

    Raises
    ------
    ValueError:
        If a job has start > finish.
    TypeError:
        If a job does not contain exactly three values or contains values
        that cannot be compared/arithmetic-operated as required.
    """

    # Validate and attach original indices.
    indexed_jobs = []

    for original_index, job in enumerate(jobs):
        if len(job) != 3:
            raise ValueError(
                f"Job at index {original_index} must contain "
                "(start, finish, profit)."
            )

        start, finish, profit = job

        if start > finish:
            raise ValueError(
                f"Job at index {original_index} has start > finish."
            )

        indexed_jobs.append(
            (start, finish, profit, original_index)
        )

    n = len(indexed_jobs)

    if n == 0:
        return 0, []

    # Sort primarily by finish time.
    # The remaining keys make the ordering fully deterministic.
    indexed_jobs.sort(
        key=lambda job: (job[1], job[0], job[3])
    )

    starts = [job[0] for job in indexed_jobs]
    finishes = [job[1] for job in indexed_jobs]
    profits = [job[2] for job in indexed_jobs]
    original_indices = [job[3] for job in indexed_jobs]

    # For every job i, find the number of jobs among [0, i)
    # whose finish time <= starts[i].
    #
    # Because jobs are sorted by finish time, bisect_right gives the
    # insertion position of starts[i] in finishes. We then cap the result
    # at i so that the current job itself is never selected as its
    # predecessor.
    predecessor = []

    for i in range(n):
        p = bisect_right(finishes, starts[i], 0, i)
        predecessor.append(p)

    # dp_profit[i]:
    #   maximum profit obtainable from the first i sorted jobs.
    #
    # dp_indices[i]:
    #   lexicographically smallest original-index sequence achieving
    #   dp_profit[i].
    #
    # Keeping the sequence explicitly makes the tie-breaking rule direct
    # and deterministic.
    dp_profit = [0] * (n + 1)
    dp_indices: List[List[int]] = [[] for _ in range(n + 1)]

    for i in range(1, n + 1):
        job_position = i - 1

        # Option 1: skip the current job.
        skip_profit = dp_profit[i - 1]
        skip_indices = dp_indices[i - 1]

        # Option 2: take the current job.
        p = predecessor[job_position]

        take_profit = dp_profit[p] + profits[job_position]
        take_indices = (
            dp_indices[p] + [original_indices[job_position]]
        )

        # Select the better option.
        if take_profit > skip_profit:
            dp_profit[i] = take_profit
            dp_indices[i] = take_indices

        elif take_profit < skip_profit:
            dp_profit[i] = skip_profit
            dp_indices[i] = skip_indices

        else:
            # Equal profit: choose lexicographically smaller sequence.
            if take_indices < skip_indices:
                dp_profit[i] = take_profit
                dp_indices[i] = take_indices
            else:
                dp_profit[i] = skip_profit
                dp_indices[i] = skip_indices

    return dp_profit[n], dp_indices[n]


def solve(jobs: Sequence[Job]) -> Tuple[int, List[int]]:
    """
    Convenience wrapper around weighted_interval_scheduling().
    """
    return weighted_interval_scheduling(jobs)


if __name__ == "__main__":
    # Example:
    #
    # Index:  0          1          2          3
    # Job:   (1,3,50)   (2,4,60)   (3,5,40)   (5,7,70)
    #
    # Job 0 and job 3 are compatible because 3 <= 5.
    #
    # Best schedule:
    #   job 0 + job 3 = 120
    #
    example_jobs = [
        (1, 3, 50),
        (2, 4, 60),
        (3, 5, 40),
        (5, 7, 70),
    ]

    maximum_profit, selected_indices = solve(example_jobs)

    print("Maximum profit:", maximum_profit)
    print("Selected job indices:", selected_indices)