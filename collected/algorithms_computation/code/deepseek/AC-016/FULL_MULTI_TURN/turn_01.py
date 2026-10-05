from heapq import heappush, heappop


def simulate_queue(jobs):
    """
    Simulate a non-preemptive single-server queue.

    Parameters
    ----------
    jobs : list of tuples
        Each job is (job_id, arrival_time, service_time, priority).

    Returns
    -------
    results : list of dict
        For each job, in original input order:
        {
            "job_id": ...,
            "arrival_time": ...,
            "service_time": ...,
            "priority": ...,
            "start_time": ...,
            "completion_time": ...,
            "waiting_time": ...
        }
    average_waiting_time : float
    """

    n = len(jobs)
    if n == 0:
        return [], 0.0

    # Keep original order for output
    original_jobs = list(jobs)

    # Sort by arrival time for deterministic event processing
    jobs_sorted = sorted(jobs, key=lambda x: (x[1], x[0]))

    time = 0
    completed = 0
    idx = 0
    ready_heap = []

    results_by_id = {}

    while completed < n:
        # Add all jobs that have arrived by current time
        while idx < n and jobs_sorted[idx][1] <= time:
            job_id, arrival, service, priority = jobs_sorted[idx]
            # Max-priority queue using negative priority.
            # Tie: earlier arrival first, then smaller job ID.
            # Since heapq is min-heap, encode:
            # (-priority, arrival, job_id, service)
            heappush(ready_heap, (-priority, arrival, job_id, service))
            idx += 1

        if not ready_heap:
            # No job available yet: jump to next arrival
            time = jobs_sorted[idx][1]
            continue

        # Select highest-priority job
        neg_priority, arrival, job_id, service = heappop(ready_heap)

        start_time = time
        completion_time = start_time + service
        waiting_time = start_time - arrival

        results_by_id[job_id] = {
            "job_id": job_id,
            "arrival_time": arrival,
            "service_time": service,
            "priority": -neg_priority,
            "start_time": start_time,
            "completion_time": completion_time,
            "waiting_time": waiting_time,
        }

        time = completion_time
        completed += 1

    # Return results in original input order
    results = [results_by_id[job[0]] for job in original_jobs]

    total_waiting = sum(r["waiting_time"] for r in results)
    average_waiting_time = total_waiting / n

    return results, average_waiting_time


if __name__ == "__main__":
    # Example jobs: (job_id, arrival_time, service_time, priority)
    jobs = [
        (1, 0, 5, 2),
        (2, 1, 3, 5),
        (3, 2, 2, 5),
        (4, 3, 4, 1),
        (5, 10, 1, 9),
    ]

    results, avg_wait = simulate_queue(jobs)

    print("Job results:")
    for r in results:
        print(
            f"Job {r['job_id']}: "
            f"arrival={r['arrival_time']}, "
            f"service={r['service_time']}, "
            f"priority={r['priority']}, "
            f"start={r['start_time']}, "
            f"completion={r['completion_time']}, "
            f"waiting={r['waiting_time']}"
        )

    print(f"\nAverage waiting time: {avg_wait:.2f}")