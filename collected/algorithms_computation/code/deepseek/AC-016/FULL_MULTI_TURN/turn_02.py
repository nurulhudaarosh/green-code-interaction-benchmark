from heapq import heappush, heappop


def simulate_queue(jobs):
    """
    Simulate a non-preemptive single-server priority queue.

    Rules:
      - Larger priority runs first.
      - Ties: earlier arrival first, then smaller job ID.
      - Non-preemptive: once started, a job runs to completion.
      - Single server: one job at a time; idle if none waiting.

    Parameters
    ----------
    jobs : list of tuples
        Each job is (job_id, arrival_time, service_time, priority).

    Returns
    -------
    results : list of dict
        One entry per input job, in original input order, with
        completion_time and waiting_time (plus supporting fields).
    average_waiting_time : float
    """
    n = len(jobs)
    if n == 0:
        return [], 0.0

    # Attach original index so identity is positional (not by job_id).
    # Sort by (arrival, job_id, original_index) for deterministic loading.
    indexed = [
        (job_id, arrival, service, priority, pos)
        for pos, (job_id, arrival, service, priority) in enumerate(jobs)
    ]
    indexed.sort(key=lambda x: (x[1], x[0], x[4]))

    time = 0
    completed = 0
    idx = 0
    ready_heap = []          # (-priority, arrival, job_id, service, pos)
    results = [None] * n

    while completed < n:
        # Load every job that has arrived by the current time.
        while idx < n and indexed[idx][1] <= time:
            job_id, arrival, service, priority, pos = indexed[idx]
            heappush(ready_heap, (-priority, arrival, job_id, service, pos))
            idx += 1

        if not ready_heap:
            # Idle until the next arrival.
            time = indexed[idx][1]
            continue

        neg_priority, arrival, job_id, service, pos = heappop(ready_heap)

        start_time = time
        completion_time = start_time + service
        waiting_time = start_time - arrival

        results[pos] = {
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

    total_waiting = sum(r["waiting_time"] for r in results)
    average_waiting_time = total_waiting / n

    return results, average_waiting_time


if __name__ == "__main__":
    # Example jobs: (job_id, arrival_time, service_time, priority)
    # Includes duplicate job_id to prove positional identity is preserved.
    jobs = [
        (1, 0, 5, 2),
        (1, 1, 3, 5),
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