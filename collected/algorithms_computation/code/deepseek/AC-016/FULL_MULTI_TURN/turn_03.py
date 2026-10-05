from heapq import heappush, heappop


def simulate_queue(jobs, include_operation_summary=False):
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
    include_operation_summary : bool, default False
        If True, also return an `operation_summary` dict describing the
        number of major computational decisions/operations made.

    Returns
    -------
    results : list of dict
        One entry per input job, in original input order, containing
        job_id, arrival_time, service_time, priority, start_time,
        completion_time, waiting_time (and, when requested,
        operation_summary attached to each result? No — see below).
    average_waiting_time : float
    operation_summary : dict, optional
        Returned only when include_operation_summary=True. Contains
        arrival_loads, idle_jumps, dispatches, total_operations.
    """
    n = len(jobs)
    if n == 0:
        if include_operation_summary:
            return [], 0.0, {
                "arrival_loads": 0,
                "idle_jumps": 0,
                "dispatches": 0,
                "total_operations": 0,
            }
        return [], 0.0

    # Positional identity so duplicate job_ids cannot collide.
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

    # Counters for the operation summary.
    arrival_loads = 0
    idle_jumps = 0
    dispatches = 0

    while completed < n:
        # Load every job that has arrived by the current time.
        while idx < n and indexed[idx][1] <= time:
            job_id, arrival, service, priority, pos = indexed[idx]
            heappush(ready_heap, (-priority, arrival, job_id, service, pos))
            idx += 1
            arrival_loads += 1

        if not ready_heap:
            # Idle until the next arrival.
            time = indexed[idx][1]
            idle_jumps += 1
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
        dispatches += 1

    total_waiting = sum(r["waiting_time"] for r in results)
    average_waiting_time = total_waiting / n

    if include_operation_summary:
        operation_summary = {
            "arrival_loads": arrival_loads,
            "idle_jumps": idle_jumps,
            "dispatches": dispatches,
            "total_operations": arrival_loads + idle_jumps + dispatches,
        }
        return results, average_waiting_time, operation_summary

    return results, average_waiting_time


if __name__ == "__main__":
    # Example jobs: (job_id, arrival_time, service_time, priority)
    jobs = [
        (1, 0, 5, 2),
        (1, 1, 3, 5),   # duplicate job_id: positional identity preserved
        (3, 2, 2, 5),
        (4, 3, 4, 1),
        (5, 10, 1, 9),
    ]

    # Original behavior (feature disabled): same two outputs as before.
    results, avg_wait = simulate_queue(jobs)

    print("Job results (original outputs):")
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

    # Feature enabled: original outputs unchanged, plus operation_summary.
    results2, avg_wait2, op_summary = simulate_queue(
        jobs, include_operation_summary=True
    )

    print("\nOperation summary:")
    print(op_summary)

    # Sanity check: original outputs identical whether or not the feature
    # is enabled, and every original field is present.
    assert results == results2
    assert abs(avg_wait - avg_wait2) < 1e-12
    for r in results2:
        for key in (
            "job_id",
            "arrival_time",
            "service_time",
            "priority",
            "start_time",
            "completion_time",
            "waiting_time",
        ):
            assert key in r