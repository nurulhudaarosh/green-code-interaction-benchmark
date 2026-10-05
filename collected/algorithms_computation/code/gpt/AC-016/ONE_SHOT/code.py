"""
Problem:
Simulate a non-preemptive single-server queue.

Rules:
- Each job has:
    job_id, arrival_time, service_time, priority
- The server handles only one job at a time.
- Larger priority runs first.
- If priorities tie, earlier arrival time runs first.
- If arrival times also tie, smaller job ID runs first.
- Once a job starts, it runs until completion (non-preemptive).

Required output:
- Completion time for every job.
- Waiting time for every job.
- Average waiting time.

Key constraints:
- Deterministic behavior.
- Preserve the original job information.
- Jobs that have already arrived are selected using:
      (-priority, arrival_time, job_id)
- If the queue is empty, the server jumps forward to the next arrival.
- Use only Python's standard library.
- No network, APIs, external services, randomness, or human interaction.

Algorithm:
1. Sort all jobs by arrival time, then by job ID.
2. Maintain a priority heap for jobs that have arrived.
3. At each step:
   - Add every job whose arrival time is <= the current server time.
   - Select the highest-priority job from the heap.
   - For ties, use earlier arrival time and then smaller job ID.
   - Run that job completely.
   - Record its completion and waiting time.
4. If no job is available, move the current time to the next arrival.
5. Compute average waiting time.

Input format:
    jobs = [
        (job_id, arrival_time, service_time, priority),
        ...
    ]

Output:
    {
        "results": [
            {
                "job_id": ...,
                "completion_time": ...,
                "waiting_time": ...
            },
            ...
        ],
        "average_waiting_time": ...
    }

The result list is returned in the original input order.
"""

import heapq


def simulate_queue(jobs):
    """
    Simulate a deterministic non-preemptive single-server priority queue.

    Parameters:
        jobs: list of tuples
            (job_id, arrival_time, service_time, priority)

    Returns:
        Dictionary containing:
            - results: completion and waiting time for every job
            - average_waiting_time
    """

    if not jobs:
        return {
            "results": [],
            "average_waiting_time": 0.0
        }

    # Sort by arrival time, then job ID.
    ordered_jobs = sorted(jobs, key=lambda job: (job[1], job[0]))

    n = len(ordered_jobs)
    index = 0
    current_time = 0

    # Heap key:
    # (-priority, arrival_time, job_id, ...)
    # Negative priority makes larger priority values come first.
    heap = []

    completion = {}
    waiting = {}

    while index < n or heap:
        # If no job is waiting, jump to the next arrival.
        if not heap and index < n and current_time < ordered_jobs[index][1]:
            current_time = ordered_jobs[index][1]

        # Add all jobs that have arrived.
        while index < n and ordered_jobs[index][1] <= current_time:
            job_id, arrival_time, service_time, priority = ordered_jobs[index]

            heapq.heappush(
                heap,
                (-priority, arrival_time, job_id, service_time)
            )

            index += 1

        # Select the highest-priority available job.
        neg_priority, arrival_time, job_id, service_time = heapq.heappop(heap)

        # Non-preemptive execution:
        # waiting = start time - arrival time.
        start_time = current_time
        waiting[job_id] = start_time - arrival_time

        current_time += service_time
        completion[job_id] = current_time

    # Return results in original input order.
    results = []

    for job_id, arrival_time, service_time, priority in jobs:
        results.append({
            "job_id": job_id,
            "completion_time": completion[job_id],
            "waiting_time": waiting[job_id]
        })

    average_waiting_time = sum(waiting.values()) / n

    return {
        "results": results,
        "average_waiting_time": average_waiting_time
    }


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

if __name__ == "__main__":

    # Test 1: Priority determines the next job.
    jobs1 = [
        (1, 0, 5, 1),
        (2, 1, 2, 3),
        (3, 2, 1, 2),
    ]

    print("Test 1:")
    print(simulate_queue(jobs1))

    # Expected:
    # Job 1 starts at 0 and finishes at 5.
    # Job 2 has the highest priority and starts at 5.
    # Job 2 finishes at 7.
    # Job 3 starts at 7 and finishes at 8.
    #
    # Waiting:
    # Job 1 = 0
    # Job 2 = 5 - 1 = 4
    # Job 3 = 7 - 2 = 5
    #
    # Average = 3.0

    # Test 2: Equal priority -> earlier arrival first.
    jobs2 = [
        (1, 0, 3, 2),
        (2, 1, 2, 2),
        (3, 2, 1, 2),
    ]

    print("\nTest 2:")
    print(simulate_queue(jobs2))

    # Expected execution order: 1, 2, 3
    # Completion times: 3, 5, 6
    # Waiting times: 0, 2, 3

    # Test 3: Equal priority and equal arrival -> smaller job ID first.
    jobs3 = [
        (5, 0, 2, 4),
        (2, 0, 1, 4),
        (3, 0, 3, 4),
    ]

    print("\nTest 3:")
    print(simulate_queue(jobs3))

    # Expected execution order: 2, 3, 5
    # Completion times:
    # Job 2 -> 1
    # Job 3 -> 4
    # Job 5 -> 6
    #
    # Waiting times:
    # Job 5 -> 4
    # Job 2 -> 0
    # Job 3 -> 1

    # Test 4: Server must wait for a future arrival.
    jobs4 = [
        (1, 5, 3, 2),
        (2, 10, 2, 1),
    ]

    print("\nTest 4:")
    print(simulate_queue(jobs4))

    # Expected:
    # Job 1 starts at 5 and finishes at 8.
    # Server waits until time 10.
    # Job 2 starts at 10 and finishes at 12.
    # Both waiting times are 0.

    # Test 5: Empty input.
    jobs5 = []

    print("\nTest 5:")
    print(simulate_queue(jobs5))