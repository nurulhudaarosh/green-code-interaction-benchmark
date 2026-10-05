# Priority Queue Simulator
#
# ORIGINAL PROBLEM:
# Simulate a non-preemptive single-server queue.
#
# Scheduling rules:
# 1. A job can be selected only after it has arrived.
# 2. Larger priority runs first.
# 3. If priorities are equal, the earlier arrival time runs first.
# 4. If both priority and arrival time are equal, the smaller job ID runs first.
# 5. The queue is non-preemptive: once a job starts, it runs until completion.
#
# ORIGINAL REQUIRED OUTPUTS:
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
# New optional feature:
# - When operation_summary is requested, return an additional
#   "operation_summary" field.
# - It contains a deterministic summary of the major computational
#   decisions/operations made by the algorithm.
# - For this task, the summary reports:
#       * jobs_processed
#       * arrival_insertions
#       * server_decisions
#       * idle_time_jumps
#       * total_major_operations
#
# The original fields and scheduling behavior remain unchanged.
# If operation_summary is disabled/not requested, the original output
# contains only "results" and "average_waiting_time".
#
# KEY CONSTRAINTS:
# - Sort arrivals before simulation.
# - Use a priority heap for server decisions.
# - Larger priority must be selected first.
# - Ties use earlier arrival, then smaller job ID.
# - Waiting time = start time - arrival time.
# - Completion time = start time + service time.
# - If the server is idle, advance time to the next arrival.
# - Output behavior must be deterministic.
# - Standard library only.
# - No network access, APIs, external services, randomness, or interaction.
#
# ALGORITHM:
# 1. Sort jobs by (arrival_time, job_id).
# 2. Insert every arrived job into a min-heap.
# 3. Store negative priority so larger priorities come out first.
# 4. Use (negative_priority, arrival_time, job_id, ...) as the heap key.
# 5. If the heap is empty, jump to the next arrival.
# 6. Pop one job and run it to completion.
# 7. Record completion and waiting times.
# 8. Count each insertion, server selection, idle jump, and completed job
#    as a deterministic major operation.
# 9. Repeat until all jobs are processed.
# 10. Compute the average waiting time.
#
# Job format:
#     (job_id, arrival_time, service_time, priority)


from heapq import heappop, heappush


def priority_queue_simulator(jobs, include_operation_summary=False):
    """
    Simulate a deterministic non-preemptive single-server priority queue.

    Parameters:
        jobs: iterable of
              (job_id, arrival_time, service_time, priority)

        include_operation_summary:
            False -> preserve the original output format.
            True  -> add the operation_summary field.

    Returns:
        Original output:
        {
            "results": [...],
            "average_waiting_time": ...
        }

        With operation summary enabled:
        {
            "results": [...],
            "average_waiting_time": ...,
            "operation_summary": {
                "jobs_processed": ...,
                "arrival_insertions": ...,
                "server_decisions": ...,
                "idle_time_jumps": ...,
                "total_major_operations": ...
            }
        }
    """

    # Sort arrivals deterministically.
    arrivals = sorted(jobs, key=lambda job: (job[1], job[0]))

    heap = []
    results = []

    current_time = 0
    next_job = 0
    total_waiting_time = 0
    n = len(arrivals)

    # Deterministic operation counters.
    jobs_processed = 0
    arrival_insertions = 0
    server_decisions = 0
    idle_time_jumps = 0

    while next_job < n or heap:

        # If no job is available, jump directly to the next arrival.
        if (
            not heap
            and next_job < n
            and current_time < arrivals[next_job][1]
        ):
            current_time = arrivals[next_job][1]
            idle_time_jumps += 1

        # Add every job that has arrived by the current time.
        while next_job < n and arrivals[next_job][1] <= current_time:
            job_id, arrival_time, service_time, priority = arrivals[next_job]

            # Min-heap:
            # negative priority -> larger priority first
            # arrival time -> earlier arrival first
            # job ID -> smaller ID first
            heappush(
                heap,
                (
                    -priority,
                    arrival_time,
                    job_id,
                    service_time,
                ),
            )

            arrival_insertions += 1
            next_job += 1

        # One server scheduling decision.
        (
            neg_priority,
            arrival_time,
            job_id,
            service_time,
        ) = heappop(heap)

        server_decisions += 1

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
        jobs_processed += 1

    # Preserve deterministic output ordering.
    results.sort(key=lambda result: result["job_id"])

    average_waiting_time = (
        total_waiting_time / n if n > 0 else 0.0
    )

    output = {
        "results": results,
        "average_waiting_time": average_waiting_time,
    }

    # Optional feature: do not change the original output when disabled.
    if include_operation_summary:
        total_major_operations = (
            jobs_processed
            + arrival_insertions
            + server_decisions
            + idle_time_jumps
        )

        output["operation_summary"] = {
            "jobs_processed": jobs_processed,
            "arrival_insertions": arrival_insertions,
            "server_decisions": server_decisions,
            "idle_time_jumps": idle_time_jumps,
            "total_major_operations": total_major_operations,
        }

    return output


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

if __name__ == "__main__":

    jobs = [
        (1, 0, 5, 2),
        (2, 1, 3, 5),
        (3, 2, 2, 5),
        (4, 6, 4, 1),
    ]

    # Original behavior: no additional field.
    result = priority_queue_simulator(jobs)

    expected_original = {
        "results": [
            {
                "job_id": 1,
                "completion_time": 5,
                "waiting_time": 0,
            },
            {
                "job_id": 2,
                "completion_time": 8,
                "waiting_time": 4,
            },
            {
                "job_id": 3,
                "completion_time": 10,
                "waiting_time": 6,
            },
            {
                "job_id": 4,
                "completion_time": 14,
                "waiting_time": 4,
            },
        ],
        "average_waiting_time": 3.5,
    }

    assert result == expected_original
    assert "operation_summary" not in result

    # New feature enabled.
    result_with_summary = priority_queue_simulator(
        jobs,
        include_operation_summary=True,
    )

    assert result_with_summary["results"] == expected_original["results"]
    assert result_with_summary["average_waiting_time"] == 3.5

    assert result_with_summary["operation_summary"] == {
        "jobs_processed": 4,
        "arrival_insertions": 4,
        "server_decisions": 4,
        "idle_time_jumps": 1,
        "total_major_operations": 13,
    }

    # Tie-breaking test:
    # Jobs 2 and 3 have equal priority and arrival time.
    # Smaller job ID must run first.
    tie_jobs = [
        (3, 0, 2, 5),
        (2, 0, 2, 5),
        (1, 0, 1, 1),
    ]

    tie_result = priority_queue_simulator(
        tie_jobs,
        include_operation_summary=True,
    )

    assert tie_result["results"] == [
        {
            "job_id": 1,
            "completion_time": 5,
            "waiting_time": 4,
        },
        {
            "job_id": 2,
            "completion_time": 2,
            "waiting_time": 0,
        },
        {
            "job_id": 3,
            "completion_time": 4,
            "waiting_time": 2,
        },
    ]

    # Empty input.
    empty_result = priority_queue_simulator(
        [],
        include_operation_summary=True,
    )

    assert empty_result == {
        "results": [],
        "average_waiting_time": 0.0,
        "operation_summary": {
            "jobs_processed": 0,
            "arrival_insertions": 0,
            "server_decisions": 0,
            "idle_time_jumps": 0,
            "total_major_operations": 0,
        },
    }

    print("All tests passed.")