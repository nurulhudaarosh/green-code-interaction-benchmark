"""
Priority Queue Simulator
========================

Original Problem
----------------
Simulate a non-preemptive single-server queue.

Each job is represented as:
    (job_id, arrival_time, service_time, priority)

Scheduling rules:
    1. Only one job can run at a time.
    2. The server is non-preemptive: once a job starts, it runs until completion.
    3. Among all jobs that have already arrived, choose:
         - larger priority first
         - if priority ties, earlier arrival first
         - if arrival also ties, smaller job ID first
    4. If no job is available, the server jumps to the next arrival time.
    5. Waiting time = start time - arrival time.
    6. Completion time = start time + service time.
    7. Return completion and waiting time for every job.
    8. Return the average waiting time.
    9. Preserve the original input order in the returned job list.
   10. All behavior must be deterministic.

Key Complexity Requirement
--------------------------
Use:
    - sorting by arrival time
    - a priority heap for server decisions

Expected complexity:
    O(n log n) time
    O(n) extra space

A worst-case-like structure for this complexity is a large collection
of jobs whose arrival times are spread so that many jobs repeatedly
enter and leave the heap. This forces both:
    - O(n log n) sorting
    - O(log n) heap insertion/removal operations

The implementation below explicitly tests such a large valid case.

Required Output
---------------
{
    "jobs": [
        {
            "job_id": ...,
            "completion_time": ...,
            "waiting_time": ...
        },
        ...
    ],
    "average_waiting_time": ...
}

Tie-breaking must remain exactly:
    higher priority
    -> earlier arrival
    -> smaller job ID
"""

from heapq import heappush, heappop
from typing import Iterable, Tuple, Dict, Any


def simulate_priority_queue(
    jobs: Iterable[Tuple[int, int, int, int]]
) -> Dict[str, Any]:
    """
    Simulate a non-preemptive single-server priority queue.

    Input job format:
        (job_id, arrival_time, service_time, priority)

    Output:
        {
            "jobs": [
                {
                    "job_id": int,
                    "completion_time": int,
                    "waiting_time": int
                },
                ...
            ],
            "average_waiting_time": float
        }

    The output jobs are kept in the same order as the input.
    """

    jobs = list(jobs)
    n = len(jobs)

    if n == 0:
        return {
            "jobs": [],
            "average_waiting_time": 0.0,
        }

    # Sort by arrival time.
    #
    # The original index is retained so that results can later be
    # restored to the original input order.
    arrival_order = sorted(
        (
            arrival_time,
            job_id,
            index,
            service_time,
            priority,
        )
        for index, (job_id, arrival_time, service_time, priority)
        in enumerate(jobs)
    )

    completion = [0] * n
    waiting = [0] * n

    # Heap key:
    #   -priority  -> larger priority first
    #   arrival    -> earlier arrival first
    #   job_id     -> smaller ID first
    #
    # The negative priority is necessary because Python's heap is
    # a min-heap.
    heap = []

    current_time = 0
    next_job = 0
    completed = 0
    total_waiting = 0

    while completed < n:

        # If no job is waiting, jump directly to the next arrival.
        if (
            not heap
            and next_job < n
            and current_time < arrival_order[next_job][0]
        ):
            current_time = arrival_order[next_job][0]

        # Add every job that has arrived by current_time.
        while (
            next_job < n
            and arrival_order[next_job][0] <= current_time
        ):
            (
                arrival_time,
                job_id,
                index,
                service_time,
                priority,
            ) = arrival_order[next_job]

            heappush(
                heap,
                (
                    -priority,
                    arrival_time,
                    job_id,
                    index,
                    service_time,
                ),
            )

            next_job += 1

        # Select the highest-priority available job.
        (
            _negative_priority,
            arrival_time,
            job_id,
            index,
            service_time,
        ) = heappop(heap)

        start_time = current_time
        waiting_time = start_time - arrival_time
        completion_time = start_time + service_time

        waiting[index] = waiting_time
        completion[index] = completion_time

        total_waiting += waiting_time
        current_time = completion_time
        completed += 1

    return {
        "jobs": [
            {
                "job_id": jobs[index][0],
                "completion_time": completion[index],
                "waiting_time": waiting[index],
            }
            for index in range(n)
        ],
        "average_waiting_time": total_waiting / n,
    }


# ============================================================
# Tests
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Test 1: Basic priority behavior
    # --------------------------------------------------------
    jobs1 = [
        (1, 0, 5, 1),
        (2, 1, 3, 2),
        (3, 2, 2, 5),
    ]

    result1 = simulate_priority_queue(jobs1)

    expected1 = {
        "jobs": [
            {"job_id": 1, "completion_time": 5, "waiting_time": 0},
            {"job_id": 2, "completion_time": 10, "waiting_time": 6},
            {"job_id": 3, "completion_time": 7, "waiting_time": 3},
        ],
        "average_waiting_time": 3.0,
    }

    assert result1 == expected1


    # --------------------------------------------------------
    # Test 2: Same arrival and same priority.
    #
    # Smaller job ID must win.
    # --------------------------------------------------------
    jobs2 = [
        (3, 0, 2, 5),
        (1, 0, 2, 5),
        (2, 0, 2, 5),
    ]

    result2 = simulate_priority_queue(jobs2)

    expected2 = {
        "jobs": [
            {"job_id": 3, "completion_time": 6, "waiting_time": 4},
            {"job_id": 1, "completion_time": 2, "waiting_time": 0},
            {"job_id": 2, "completion_time": 4, "waiting_time": 2},
        ],
        "average_waiting_time": 2.0,
    }

    assert result2 == expected2


    # --------------------------------------------------------
    # Test 3: Server initially idle.
    # --------------------------------------------------------
    jobs3 = [
        (10, 5, 4, 1),
        (20, 10, 3, 2),
    ]

    result3 = simulate_priority_queue(jobs3)

    expected3 = {
        "jobs": [
            {"job_id": 10, "completion_time": 9, "waiting_time": 0},
            {"job_id": 20, "completion_time": 13, "waiting_time": 0},
        ],
        "average_waiting_time": 0.0,
    }

    assert result3 == expected3


    # --------------------------------------------------------
    # Test 4: Empty input.
    # --------------------------------------------------------
    result4 = simulate_priority_queue([])

    assert result4 == {
        "jobs": [],
        "average_waiting_time": 0.0,
    }


    # --------------------------------------------------------
    # Test 5: Higher priority wins over earlier arrival.
    #
    # Job 2 arrives before Job 3, but Job 3 has higher priority.
    # Both are waiting when Job 1 completes.
    # --------------------------------------------------------
    jobs5 = [
        (1, 0, 4, 1),
        (2, 1, 2, 10),
        (3, 2, 1, 20),
    ]

    result5 = simulate_priority_queue(jobs5)

    expected5 = {
        "jobs": [
            {"job_id": 1, "completion_time": 4, "waiting_time": 0},
            {"job_id": 2, "completion_time": 7, "waiting_time": 4},
            {"job_id": 3, "completion_time": 5, "waiting_time": 2},
        ],
        "average_waiting_time": 2.0,
    }

    assert result5 == expected5


    # --------------------------------------------------------
    # Test 6: Explicit tie-breaking chain.
    #
    # Jobs 2 and 3:
    #   same priority
    #   different arrival times
    #
    # Earlier arrival must win.
    #
    # Jobs 4 and 5:
    #   same priority
    #   same arrival
    #
    # Smaller ID must win.
    # --------------------------------------------------------
    jobs6 = [
        (1, 0, 1, 1),
        (2, 0, 3, 7),
        (3, 1, 2, 7),
        (5, 1, 1, 7),
        (4, 1, 1, 7),
    ]

    result6 = simulate_priority_queue(jobs6)

    # Execution order:
    # Job 1 -> Job 2 -> Job 3 -> Job 4 -> Job 5
    #
    # Job 2 and Job 3 have equal priority, so Job 2 wins
    # because it arrived earlier.
    #
    # Job 4 and Job 5 have equal priority and arrival,
    # so Job 4 wins because its ID is smaller.
    expected6 = {
        "jobs": [
            {"job_id": 1, "completion_time": 1, "waiting_time": 0},
            {"job_id": 2, "completion_time": 4, "waiting_time": 1},
            {"job_id": 3, "completion_time": 6, "waiting_time": 3},
            {"job_id": 5, "completion_time": 8, "waiting_time": 7},
            {"job_id": 4, "completion_time": 7, "waiting_time": 6},
        ],
        "average_waiting_time": 3.4,
    }

    assert result6 == expected6


    # --------------------------------------------------------
    # Test 7: Worst-case-like O(n log n) structure.
    #
    # Large valid input:
    # - 5,000 jobs
    # - all jobs arrive at time 0
    # - every job enters the heap
    # - every job is then removed from the heap
    #
    # This creates a large heap and forces O(log n) heap
    # insertion/removal work repeatedly.
    #
    # The input is deliberately reversed by job ID so the
    # implementation cannot rely on the input already being sorted.
    # --------------------------------------------------------
    n = 5000

    large_jobs = [
        (
            job_id,
            0,
            1,
            job_id,
        )
        for job_id in range(n, 0, -1)
    ]

    large_result = simulate_priority_queue(large_jobs)

    # Highest priority is the largest job ID, so execution order is:
    # 5000, 4999, ..., 1.
    #
    # Every service time is 1.
    # Therefore:
    #   job 5000 -> completion 1, waiting 0
    #   job 4999 -> completion 2, waiting 1
    #   ...
    #   job 1    -> completion 5000, waiting 4999
    #
    # The output itself must still follow the original input order:
    # 5000, 4999, ..., 1.
    assert len(large_result["jobs"]) == n

    for position, job in enumerate(large_result["jobs"]):
        expected_job_id = n - position
        expected_completion = position + 1
        expected_waiting = position

        assert job["job_id"] == expected_job_id
        assert job["completion_time"] == expected_completion
        assert job["waiting_time"] == expected_waiting

    expected_average = (n - 1) / 2
    assert large_result["average_waiting_time"] == expected_average


    # --------------------------------------------------------
    # Test 8: Large structure with repeated priorities and
    # repeated arrival times.
    #
    # This stresses all heap tie-breaking levels:
    #   priority -> arrival -> job ID
    # --------------------------------------------------------
    n2 = 3000

    large_tie_jobs = [
        (
            job_id,
            job_id // 3,
            1,
            job_id % 5,
        )
        for job_id in range(n2, 0, -1)
    ]

    large_tie_result = simulate_priority_queue(large_tie_jobs)

    assert len(large_tie_result["jobs"]) == n2

    # Verify that every job appears exactly once and that every
    # reported time is valid.
    returned_ids = [job["job_id"] for job in large_tie_result["jobs"]]

    assert returned_ids == [
        job[0] for job in large_tie_jobs
    ]

    for job in large_tie_result["jobs"]:
        assert job["completion_time"] >= 0
        assert job["waiting_time"] >= 0

    # Average waiting time must agree with the individual results.
    total_waiting = sum(
        job["waiting_time"]
        for job in large_tie_result["jobs"]
    )

    assert large_tie_result["average_waiting_time"] == (
        total_waiting / n2
    )


    print("All tests passed.")
    print("Worst-case-like O(n log n) test passed for 5,000 jobs.")