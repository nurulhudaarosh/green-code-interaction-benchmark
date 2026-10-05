# Problem: Priority Queue Simulator
#
# Simulate a non-preemptive single-server queue.
#
# Rules:
# 1. Jobs become available at their arrival time.
# 2. When the server becomes free, choose the available job with:
#       - larger priority first,
#       - earlier arrival time if priorities are equal,
#       - smaller job ID if both priority and arrival time are equal.
# 3. Once a job starts, it runs until completion (non-preemptive).
# 4. Return completion time and waiting time for every job.
# 5. Return the average waiting time.
#
# Key constraints:
# - Use deterministic behavior.
# - Sort jobs by arrival time before simulation.
# - Use a priority heap for server decisions.
# - The heap must enforce the required priority order exactly.
# - Waiting time = start time - arrival time.
# - Completion time = start time + service/burst time.
# - If the server is idle, advance the current time to the next arrival.
# - Use only the Python standard library.
# - No network access, APIs, external services, randomness, or human interaction.
#
# Required output:
# {
#     "results": [
#         {
#             "job_id": ...,
#             "completion_time": ...,
#             "waiting_time": ...
#         },
#         ...
#     ],
#     "average_waiting_time": ...
# }
#
# Algorithm:
# 1. Sort all jobs by (arrival_time, job_id).
# 2. Keep a min-heap containing currently available jobs.
# 3. Because Python's heap is a min-heap, store negative priority so that
#    larger priorities are selected first.
# 4. Use (negative_priority, arrival_time, job_id, ...) as the heap key.
# 5. If the heap is empty, move the current time to the next job's arrival.
# 6. Add every job that has arrived by the current time to the heap.
# 7. Pop the highest-priority job and run it to completion.
# 8. Record its completion and waiting times.
# 9. Repeat until every job has been processed.
# 10. Compute the average waiting time.
#
# Each job is expected to be represented as:
# (job_id, arrival_time, service_time, priority)

from heapq import heappop, heappush


def priority_queue_simulator(jobs):
    """
    Simulate a deterministic non-preemptive single-server priority queue.

    Parameters:
        jobs: iterable of tuples
              (job_id, arrival_time, service_time, priority)

    Returns:
        dict containing:
            - results: completion and waiting time for every job
            - average_waiting_time
    """

    # Sort arrivals deterministically.
    arrivals = sorted(jobs, key=lambda job: (job[1], job[0]))

    heap = []
    results = []

    current_time = 0
    next_job = 0
    total_waiting_time = 0
    n = len(arrivals)

    while next_job < n or heap:
        # If no job is currently available, jump to the next arrival.
        if not heap and next_job < n and current_time < arrivals[next_job][1]:
            current_time = arrivals[next_job][1]

        # Add every job that has arrived.
        while next_job < n and arrivals[next_job][1] <= current_time:
            job_id, arrival_time, service_time, priority = arrivals[next_job]

            # Python heap is a min-heap:
            # -priority gives larger priority first.
            heappush(
                heap,
                (
                    -priority,
                    arrival_time,
                    job_id,
                    service_time,
                ),
            )

            next_job += 1

        # Select the job according to:
        # larger priority -> earlier arrival -> smaller job ID.
        neg_priority, arrival_time, job_id, service_time = heappop(heap)

        start_time = current_time
        waiting_time = start_time - arrival_time

        current_time += service_time
        completion_time = current_time

        results.append(
            {
                "job_id": job_id,
                "completion_time": completion_time,
                "waiting_time": waiting_time,
            }
        )

        total_waiting_time += waiting_time

    # Return results in job-ID order so output is deterministic and easy
    # to associate with the original jobs.
    results.sort(key=lambda result: result["job_id"])

    average_waiting_time = (
        total_waiting_time / n if n > 0 else 0.0
    )

    return {
        "results": results,
        "average_waiting_time": average_waiting_time,
    }


# Example
if __name__ == "__main__":
    jobs = [
        (1, 0, 5, 2),
        (2, 1, 3, 5),
        (3, 2, 2, 5),
        (4, 6, 4, 1),
    ]

    print(priority_queue_simulator(jobs))

    # Expected:
    # Job 1 starts at 0 and completes at 5.
    # At time 5, jobs 2 and 3 are available.
    # Both have priority 5, so job 2 arrived earlier and runs first.
    # Job 2 completes at 8.
    # Job 3 then completes at 10.
    # Job 4 starts at 10 and completes at 14.
    #
    # Waiting times:
    # Job 1: 0
    # Job 2: 4
    # Job 3: 6
    # Job 4: 4
    #
    # Average waiting time = 14 / 4 = 3.5