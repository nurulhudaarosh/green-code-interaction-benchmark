"""
Problem:
Simulate a non-preemptive single-server queue.

Rules:
1. A job can start only when the server is free.
2. Among all jobs that have already arrived, the job with larger
   priority runs first.
3. If priorities are equal, earlier arrival time runs first.
4. If arrival times are also equal, smaller job ID runs first.
5. Once a job starts, it runs until completion (non-preemptive).
6. Return the completion time and waiting time for every job, plus
   the average waiting time.

Key constraints:
- Deterministic behavior is required.
- Jobs may arrive while another job is being processed.
- The server may become idle when no job has arrived yet.
- Waiting time = start time - arrival time.
- Completion time = start time + service time.
- Only the Python standard library is used.
- No network, APIs, external services, randomness, or human interaction.

Required output:
{
    "jobs": {
        job_id: {
            "completion_time": ...,
            "waiting_time": ...
        },
        ...
    },
    "average_waiting_time": ...
}

Algorithm:
1. Sort all jobs by arrival time.
2. Maintain a priority heap containing jobs that have arrived.
3. Python's heap is a min-heap, so use negative priority to make larger
   priorities come first.
4. For equal priorities, use arrival time and job ID as the next keys.
5. If the heap is empty, jump the current time to the next arrival.
6. Otherwise, remove the highest-priority available job and execute it
   completely.
7. Record its completion and waiting time.
8. Continue until every job has been processed.

Heap ordering:
(-priority, arrival_time, job_id)

This directly implements:
larger priority -> earlier arrival -> smaller job ID.
"""

import heapq


def simulate_queue(jobs):
    """
    Simulate a non-preemptive single-server priority queue.

    Input:
        jobs: iterable of tuples
              (job_id, arrival_time, service_time, priority)

    Output:
        {
            "jobs": {
                job_id: {
                    "completion_time": completion_time,
                    "waiting_time": waiting_time
                },
                ...
            },
            "average_waiting_time": average_waiting_time
        }
    """

    jobs = list(jobs)

    if not jobs:
        return {
            "jobs": {},
            "average_waiting_time": 0.0
        }

    # Sort arrivals deterministically.
    arrivals = sorted(jobs, key=lambda job: (job[1], job[0]))

    heap = []
    result = {}

    current_time = 0
    next_job = 0
    total_waiting_time = 0
    completed = 0

    while completed < len(arrivals):

        # If no job is available, move directly to the next arrival.
        if not heap and current_time < arrivals[next_job][1]:
            current_time = arrivals[next_job][1]

        # Add every job that has arrived by current_time.
        while next_job < len(arrivals) and arrivals[next_job][1] <= current_time:
            job_id, arrival_time, service_time, priority = arrivals[next_job]

            heapq.heappush(
                heap,
                (-priority, arrival_time, job_id, service_time)
            )

            next_job += 1

        # Select the job according to:
        # larger priority -> earlier arrival -> smaller job ID.
        neg_priority, arrival_time, job_id, service_time = heapq.heappop(heap)

        start_time = current_time
        waiting_time = start_time - arrival_time

        current_time += service_time
        completion_time = current_time

        result[job_id] = {
            "completion_time": completion_time,
            "waiting_time": waiting_time
        }

        total_waiting_time += waiting_time
        completed += 1

    average_waiting_time = total_waiting_time / len(arrivals)

    return {
        "jobs": result,
        "average_waiting_time": average_waiting_time
    }


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

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

    print("Test 1:")
    print(simulate_queue(jobs1))

    expected1 = {
        "jobs": {
            1: {"completion_time": 5, "waiting_time": 0},
            3: {"completion_time": 7, "waiting_time": 3},
            2: {"completion_time": 10, "waiting_time": 6},
        },
        "average_waiting_time": 3.0,
    }

    assert simulate_queue(jobs1) == expected1

    # Test 2:
    # Same priority and same arrival time.
    # Smaller job ID must run first.
    jobs2 = [
        (3, 0, 2, 5),
        (1, 0, 3, 5),
        (2, 0, 1, 5),
    ]

    print("\nTest 2:")
    print(simulate_queue(jobs2))

    expected2 = {
        "jobs": {
            1: {"completion_time": 3, "waiting_time": 0},
            2: {"completion_time": 4, "waiting_time": 3},
            3: {"completion_time": 6, "waiting_time": 4},
        },
        "average_waiting_time": 7 / 3,
    }

    assert simulate_queue(jobs2) == expected2

    # Test 3:
    # The server is initially idle, so it jumps to time 5.
    jobs3 = [
        (10, 5, 4, 1),
        (20, 10, 2, 3),
    ]

    print("\nTest 3:")
    print(simulate_queue(jobs3))

    expected3 = {
        "jobs": {
            10: {"completion_time": 9, "waiting_time": 0},
            20: {"completion_time": 12, "waiting_time": 0},
        },
        "average_waiting_time": 0.0,
    }

    assert simulate_queue(jobs3) == expected3

    print("\nAll tests passed.")