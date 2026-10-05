import heapq
from typing import List, Tuple, Dict


def simulate_queue(jobs: List[Tuple[int, int, int, int]]) -> Dict:
    """
    jobs: list of (job_id, arrival, burst, priority)
    Returns a dict with per-job results and the average waiting time.
    """
    order = sorted(jobs, key=lambda j: (j[1], j[0]))  # by arrival, then id
    n = len(order)
    heap = []            # entries: (-priority, arrival, job_id, burst)
    results = {}         # job_id -> {"completion": int, "waiting": int}
    clock = 0
    i = 0
    done = 0

    while done < n:
        # Admit every job that has arrived by the current time
        while i < n and order[i][1] <= clock:
            jid, arr, burst, pri = order[i]
            heapq.heappush(heap, (-pri, arr, jid, burst))
            i += 1

        if not heap:
            # Server idle: jump to the next arrival
            clock = order[i][1]
            continue

        neg_pri, arr, jid, burst = heapq.heappop(heap)
        start = clock
        clock = start + burst
        results[jid] = {"completion": clock, "waiting": start - arr}
        done += 1

    total_wait = sum(r["waiting"] for r in results.values())
    avg_wait = total_wait / n if n else 0.0
    return {"jobs": results, "average_waiting": avg_wait}


if __name__ == "__main__":
    # (job_id, arrival, burst, priority)
    sample = [
        (1, 0, 5, 1),
        (2, 1, 3, 3),
        (3, 2, 2, 3),
        (4, 3, 4, 2),
        (5, 20, 1, 1),
    ]
    out = simulate_queue(sample)
    for jid in sorted(out["jobs"]):
        r = out["jobs"][jid]
        print(f"Job {jid}: completion={r['completion']}, waiting={r['waiting']}")
    print(f"Average waiting time: {out['average_waiting']:.4f}")