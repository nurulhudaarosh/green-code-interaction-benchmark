import heapq
from typing import Dict, List, Tuple

Job = Tuple[int, float, float, int]  # (job_id, arrival, burst, priority)


def simulate_queue(jobs: List[Job]):
    """
    Non-preemptive single-server priority queue simulation.

    Returns:
        results: dict job_id -> {"completion": ..., "waiting": ...}
        avg_waiting: float (0.0 if there are no jobs)
        order: list of job IDs in execution order
    """
    if not jobs:
        return {}, 0.0, []

    # Sort arrivals; job ID breaks arrival ties for deterministic ingestion.
    pending = sorted(jobs, key=lambda j: (j[1], j[0]))
    n = len(pending)

    heap: List[Tuple[int, float, int, float]] = []
    results: Dict[int, Dict[str, float]] = {}
    order: List[int] = []

    t = 0
    i = 0          # next job in `pending` to arrive
    done = 0
    total_wait = 0

    while done < n:
        # Admit every job that has arrived by time t.
        while i < n and pending[i][1] <= t:
            jid, arr, burst, prio = pending[i]
            # Larger priority first -> negate; then earlier arrival; then smaller ID.
            heapq.heappush(heap, (-prio, arr, jid, burst))
            i += 1

        if not heap:
            # Server idle: jump to the next arrival.
            t = pending[i][1]
            continue

        neg_prio, arr, jid, burst = heapq.heappop(heap)
        start = t
        completion = start + burst
        waiting = start - arr

        results[jid] = {"completion": completion, "waiting": waiting}
        order.append(jid)
        total_wait += waiting
        t = completion
        done += 1

    avg_waiting = total_wait / n
    return results, avg_waiting, order


if __name__ == "__main__":
    # (id, arrival, burst, priority)
    sample = [
        (1, 0, 5, 1),
        (2, 1, 3, 3),
        (3, 2, 2, 3),
        (4, 2, 4, 2),
        (5, 20, 1, 1),
    ]
    res, avg, order = simulate_queue(sample)
    print("Execution order:", order)
    for jid in sorted(res):
        r = res[jid]
        print(f"Job {jid}: completion={r['completion']}, waiting={r['waiting']}")
    print(f"Average waiting time: {avg:.4f}")