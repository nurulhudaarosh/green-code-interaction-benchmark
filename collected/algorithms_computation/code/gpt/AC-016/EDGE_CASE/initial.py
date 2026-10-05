"""
Problem Restatement
-------------------
Simulate a non-preemptive single-server queue.

Each job has:
    - job_id
    - arrival time
    - service/burst time
    - priority

Rules:
    1. The server can process only one job at a time.
    2. Once a job starts, it runs until completion (non-preemptive).
    3. When the server becomes free, choose among all arrived jobs:
       - larger priority first
       - if priorities tie, earlier arrival first
       - if arrival times also tie, smaller job ID first
    4. If no job has arrived, the server jumps forward to the next
       arrival time.
    5. Return completion time and waiting time for every job.
    6. Return the average waiting time.

Key Constraints / Requirements
------------------------------
- Deterministic behavior.
- Preserve the original job order in the output.
- Use a sorted arrival list.
- Use a priority heap for server decisions.
- The priority heap must implement:
      higher priority -> earlier choice
      earlier arrival -> earlier choice
      smaller job ID -> earlier choice
- The queue is non-preemptive.
- Jobs with the same arrival time must still be handled deterministically.
- Waiting time = start time - arrival time.
- Completion time = start time + service time.
- Average waiting time = total waiting time / number of jobs.
- Use only Python's standard library.
- No network access, APIs, external services, randomness, or human interaction.

Required Output
---------------
A dictionary containing:
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

The jobs list follows the original input order.


Algorithm
---------
1. Sort job indices by (arrival_time, job_id).
2. Keep a min-heap of currently available jobs.
3. Store (-priority, arrival_time, job_id, index) in the heap so that
   Python's min-heap selects:
       - largest priority
       - earliest arrival
       - smallest job ID
4. Maintain the current server time.
5. Add every job that has arrived by the current time to the heap.
6. If the heap is empty, jump the current time to the next job's arrival.
7. Pop the highest-priority job and process it completely.
8. Calculate its waiting and completion times.
9. Repeat until every job is processed.
10. Compute the average waiting time.

Time Complexity
---------------
Sorting: O(n log n)
Each job is inserted into and removed from the heap once:
O(n log n)

Overall: O(n log n)
Space: O(n)


Implementation
--------------
"""

from heapq import heappush, heappop
from typing import Iterable, Tuple, Dict, Any


def simulate_priority_queue(
    jobs: Iterable[Tuple[int, int, int, int]]
) -> Dict[str, Any]:
    """
    Simulate a non-preemptive single-server priority queue.

    Each input job is:
        (job_id, arrival_time, service_time, priority)

    Returns:
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

    The returned jobs remain in the same order as the input.
    """

    jobs = list(jobs)
    n = len(jobs)

    if n == 0:
        return {
            "jobs": [],
            "average_waiting_time": 0.0,
        }

    # Store:
    # (arrival_time, job_id, original_index, service_time, priority)
    #
    # job_id is included in the sorting key to make equal-arrival
    # handling deterministic.
    arrival_order = sorted(
        (
            arrival_time,
            job_id,
            index,
            service_time,
            priority,
        )
        for index, (job_id, arrival_time, service_time, priority) in enumerate(jobs)
    )

    completion = [0] * n
    waiting = [0] * n

    heap = []
    current_time = 0
    next_job = 0
    completed = 0
    total_waiting = 0

    while completed < n:

        # If no job is currently available, jump to the next arrival.
        if not heap and next_job < n and current_time < arrival_order[next_job][0]:
            current_time = arrival_order[next_job][0]

        # Add all jobs that have arrived.
        while (
            next_job < n
            and arrival_order[next_job][0] <= current_time
        ):
            arrival_time, job_id, index, service_time, priority = arrival_order[next_job]

            # Python's heap is a min-heap.
            # Negating priority makes larger priorities come first.
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

        # Select the next job according to:
        # higher priority -> earlier arrival -> smaller job ID.
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

    result_jobs = []

    for index, (job_id, _arrival, _service, _priority) in enumerate(jobs):
        result_jobs.append(
            {
                "job_id": job_id,
                "completion_time": completion[index],
                "waiting_time": waiting[index],
            }
        )

    return {
        "jobs": result_jobs,
        "average_waiting_time": total_waiting / n,
    }


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

if __name__ == "__main__":

    # Test 1:
    # Job 1 starts first because it is the only available job.
    # While Job 1 runs, Jobs 2 and 3 arrive.
    # Job 3 has higher priority, so it runs before Job 2.
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

    # Test 2:
    # Same priority and same arrival time.
    # Smaller job ID must be selected first.
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

    # Test 3:
    # The server is initially idle, so it jumps to the first arrival.
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

    # Test 4:
    # Empty input.
    result4 = simulate_priority_queue([])

    assert result4 == {
        "jobs": [],
        "average_waiting_time": 0.0,
    }

    # Test 5:
    # Higher priority wins even when it arrived later,
    # provided both jobs are waiting when the server becomes free.
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

    print("All tests passed.")