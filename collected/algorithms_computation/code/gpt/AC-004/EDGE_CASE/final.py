"""
Weighted Job Scheduler
======================

Original problem
----------------
Given jobs with:
    - start time
    - finish time
    - profit

select a non-overlapping subset of jobs with maximum total profit.

Compatibility rule:
    If one job finishes exactly when another job starts, they are
    compatible. In other words:

        previous_finish <= next_start

Tie-breaking rule:
    If multiple schedules have the same maximum profit, return the
    schedule whose sequence of original job indices is lexicographically
    smallest.

Required output:
    {
        "max_profit": <maximum achievable profit>,
        "selected_indices": <selected original indices>
    }

Algorithm
---------
1. Sort jobs by finish time.
2. For every job, use binary search to find the latest compatible
   predecessor.
3. Use dynamic programming to choose between:
       - excluding the current job
       - including the current job
4. On equal profit, choose the lexicographically smaller sequence of
   original indices.

Complexity
----------
Sorting:
    O(n log n)

Predecessor binary searches:
    O(n log n)

Dynamic programming:
    O(n)

Total:
    O(n log n)

Space:
    O(n)

The implementation avoids constructing large copied index lists during
every DP comparison. Each DP schedule is represented by a persistent
linked structure, so extending a schedule costs O(1).

For deterministic exact tie-breaking, schedules are compared using
their original-index sequences. The comparison routine walks the
persistent representation only when two equal-profit candidates need
to be distinguished.

The public output remains exactly:
    {
        "max_profit": ...,
        "selected_indices": [...]
    }

Only the standard library is used.
No network access, APIs, external services, randomness, or interaction
are required.
"""

from bisect import bisect_right
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


Job = Tuple[float, float, float]


@dataclass(frozen=True)
class _Node:
    """
    Persistent representation of a selected-index sequence.

    `parent` points to the sequence before `index` was appended.
    """
    parent: Optional["_Node"]
    index: int
    length: int


_EMPTY: Optional[_Node] = None


def _sequence_to_list(node: Optional[_Node]) -> List[int]:
    """Convert a persistent sequence to the required output list."""
    result: List[int] = []

    while node is not None:
        result.append(node.index)
        node = node.parent

    result.reverse()
    return result


def _sequence_to_tuple(node: Optional[_Node]) -> Tuple[int, ...]:
    """Convert a persistent sequence to a tuple for exact comparison."""
    return tuple(_sequence_to_list(node))


def _better(
    profit_a: float,
    sequence_a: Optional[_Node],
    profit_b: float,
    sequence_b: Optional[_Node],
) -> Tuple[float, Optional[_Node]]:
    """
    Return the better of two schedules.

    Higher profit wins.

    If profits are equal, the lexicographically smaller sequence of
    original indices wins.
    """
    if profit_a > profit_b:
        return profit_a, sequence_a

    if profit_b > profit_a:
        return profit_b, sequence_b

    # Exact deterministic tie-breaking.
    #
    # The conversion happens only when profits are equal, rather than
    # for every DP transition.
    tuple_a = _sequence_to_tuple(sequence_a)
    tuple_b = _sequence_to_tuple(sequence_b)

    if tuple_a <= tuple_b:
        return profit_a, sequence_a

    return profit_b, sequence_b


def weighted_job_scheduler(jobs: Sequence[Job]) -> Dict[str, Any]:
    """
    Compute the maximum-profit non-overlapping job schedule.

    Args:
        jobs:
            Sequence of (start, finish, profit).

    Returns:
        {
            "max_profit": maximum achievable profit,
            "selected_indices": lexicographically smallest original-index
                                sequence among maximum-profit schedules
        }

    Raises:
        ValueError:
            If a job does not contain exactly three values or if
            start > finish.
    """

    indexed_jobs: List[Tuple[float, float, float, int]] = []

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

    # Empty input.
    if not indexed_jobs:
        return {
            "max_profit": 0,
            "selected_indices": [],
        }

    # Finish-time ordering is the standard weighted-interval-scheduling
    # ordering. Original index provides deterministic ordering when finish
    # times are equal.
    indexed_jobs.sort(
        key=lambda job: (job[1], job[3])
    )

    n = len(indexed_jobs)

    finish_times = [
        job[1]
        for job in indexed_jobs
    ]

    # predecessor[i] is the largest j < i such that:
    #
    #     finish[j] <= start[i]
    #
    # bisect_right is required because endpoint touching is compatible.
    predecessors = [-1] * n

    for i, (start, _, _, _) in enumerate(indexed_jobs):
        predecessors[i] = (
            bisect_right(finish_times, start, 0, i) - 1
        )

    # dp_profit[i] and dp_sequence[i] represent the optimal schedule
    # among the first i sorted jobs.
    dp_profit: List[float] = [0] * (n + 1)
    dp_sequence: List[Optional[_Node]] = [_EMPTY] * (n + 1)

    for i in range(n):
        start, finish, profit, original_index = indexed_jobs[i]

        # Option 1: do not select this job.
        exclude_profit = dp_profit[i]
        exclude_sequence = dp_sequence[i]

        # Option 2: select this job.
        pred = predecessors[i]

        include_profit = dp_profit[pred + 1] + profit

        include_sequence = _Node(
            parent=dp_sequence[pred + 1],
            index=original_index,
            length=(
                0
                if dp_sequence[pred + 1] is None
                else dp_sequence[pred + 1].length
            ) + 1,
        )

        best_profit, best_sequence = _better(
            exclude_profit,
            exclude_sequence,
            include_profit,
            include_sequence,
        )

        dp_profit[i + 1] = best_profit
        dp_sequence[i + 1] = best_sequence

    return {
        "max_profit": dp_profit[n],
        "selected_indices": _sequence_to_list(dp_sequence[n]),
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _run_tests() -> None:
    """Run deterministic tests covering normal and difficult cases."""

    # 1. Empty input.
    assert weighted_job_scheduler([]) == {
        "max_profit": 0,
        "selected_indices": [],
    }

    # 2. Single job.
    assert weighted_job_scheduler([
        (1, 3, 10),
    ]) == {
        "max_profit": 10,
        "selected_indices": [0],
    }

    # 3. Endpoint touching must be allowed.
    jobs = [
        (1, 3, 10),  # 0
        (3, 5, 20),  # 1
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 30,
        "selected_indices": [0, 1],
    }

    # 4. A longer incompatible job loses to two compatible jobs.
    jobs = [
        (1, 10, 15),  # 0
        (1, 5, 8),    # 1
        (5, 10, 9),   # 2
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 17,
        "selected_indices": [1, 2],
    }

    # 5. Equal-profit tie must select the lexicographically smallest
    # original-index sequence.
    #
    # Schedules:
    #     [0] -> profit 10
    #     [1] -> profit 10
    #
    # [0] is lexicographically smaller.
    jobs = [
        (1, 3, 10),  # 0
        (1, 3, 10),  # 1
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 10,
        "selected_indices": [0],
    }

    # 6. Equal-profit multi-job tie.
    #
    # Schedule A: [0, 2]
    # Schedule B: [1, 3]
    #
    # Both have profit 20, and [0, 2] is lexicographically smaller.
    jobs = [
        (1, 2, 10),  # 0
        (1, 2, 10),  # 1
        (2, 3, 10),  # 2
        (2, 3, 10),  # 3
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 20,
        "selected_indices": [0, 2],
    }

    # 7. Zero-profit jobs.
    #
    # The empty schedule has the same profit as selecting a zero-profit
    # job. Since [] is lexicographically smaller than [0], the empty
    # schedule must win.
    jobs = [
        (1, 2, 0),
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 0,
        "selected_indices": [],
    }

    # 8. Negative-profit job should never be selected when an empty
    # schedule is allowed.
    jobs = [
        (1, 2, -5),
        (2, 3, -10),
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 0,
        "selected_indices": [],
    }

    # 9. Negative values can occur alongside profitable jobs.
    jobs = [
        (1, 2, 10),   # 0
        (2, 3, -100), # 1
        (3, 4, 10),   # 2
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 20,
        "selected_indices": [0, 2],
    }

    # 10. Same finish times with deterministic behavior.
    jobs = [
        (1, 5, 10),  # 0
        (2, 5, 20),  # 1
        (3, 5, 20),  # 2
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 20,
        "selected_indices": [1],
    }

    # 11. Jobs with the same start and finish.
    jobs = [
        (5, 5, 10),  # 0
        (5, 5, 10),  # 1
        (5, 5, 5),   # 2
    ]

    # Only one of these zero-duration jobs needs to be selected for the
    # maximum profit, and index 0 is the smallest index.
    assert weighted_job_scheduler(jobs) == {
        "max_profit": 10,
        "selected_indices": [0],
    }

    # 12. Unsorted input must still produce the correct original indices.
    jobs = [
        (5, 7, 10),  # 0
        (1, 3, 30),  # 1
        (3, 5, 20),  # 2
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 60,
        "selected_indices": [1, 2, 0],
    }

    # 13. Difficult predecessor-boundary case.
    #
    # Many jobs have finish times exactly equal to later start times.
    # This specifically exercises bisect_right and the <= compatibility
    # rule.
    jobs = [
        (0, 1, 1),
        (1, 2, 1),
        (2, 3, 1),
        (3, 4, 1),
        (4, 5, 1),
        (5, 6, 1),
    ]

    assert weighted_job_scheduler(jobs) == {
        "max_profit": 6,
        "selected_indices": [0, 1, 2, 3, 4, 5],
    }

    # 14. Worst-case-like structure for the O(n log n) components.
    #
    # Large number of jobs, all overlapping heavily, forces:
    #     - O(n log n) sorting
    #     - O(n log n) predecessor searches
    #
    # None of these jobs can be combined because every job starts at 0
    # and ends at a positive time.
    #
    # The best job has the largest profit.
    n = 10_000

    jobs = [
        (0, i + 1, i + 1)
        for i in range(n)
    ]

    result = weighted_job_scheduler(jobs)

    assert result == {
        "max_profit": n,
        "selected_indices": [n - 1],
    }

    # 15. Large chain of endpoint-touching jobs.
    #
    # Every job can be selected, creating a long optimal sequence.
    # This exercises predecessor lookup repeatedly at its boundary.
    n = 10_000

    jobs = [
        (i, i + 1, 1)
        for i in range(n)
    ]

    result = weighted_job_scheduler(jobs)

    assert result["max_profit"] == n
    assert result["selected_indices"] == list(range(n))

    # 16. Large equal-profit tie case.
    #
    # Every job overlaps every other job, so all single-job schedules
    # have the same maximum profit. The smallest original index must
    # always be selected.
    n = 10_000

    jobs = [
        (0, 100, 1)
        for _ in range(n)
    ]

    result = weighted_job_scheduler(jobs)

    assert result == {
        "max_profit": 1,
        "selected_indices": [0],
    }

    print("All tests passed.")


def main() -> None:
    """
    Run the built-in deterministic test suite.
    """
    _run_tests()


if __name__ == "__main__":
    main()