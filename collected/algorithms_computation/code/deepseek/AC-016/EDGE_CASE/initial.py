import heapq
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Job:
    job_id: int
    arrival_time: int
    burst_time: int
    priority: int


def simulate_nonpreemptive_priority_queue(
    jobs: List[Job],
) -> Tuple[List[Tuple[int, int, int]], float]:
    """
    Simulate a non-preemptive single-server priority queue.

    Selection rule when the server is free:
      1. Larger `priority` first.
      2. Tie -> earlier `arrival_time`.
      3. Tie -> smaller `job_id`.

    Returns
    -------
    results : list of (job_id, completion_time, waiting_time), ordered by job_id
    avg_wait : float, average waiting time over all jobs
    """
    if not jobs:
        return [], 0.0

    # Feed jobs in arrival order; tie-break on job_id for determinism.
    arrivals = sorted(jobs, key=lambda j: (j.arrival_time, j.job_id))

    # Min-heap keyed by (-priority, arrival_time, job_id).
    # Negating priority makes heapq pop the largest priority first.
    ready: List[Tuple[int, int, int, int]] = []  # (neg_priority, arrival, id, burst)

    current_time = 0
    idx = 0
    n = len(arrivals)
    completion: dict[int, int] = {}
    waiting: dict[int, int] = {}

    while idx < n or ready:
        # Admit all jobs that have arrived by now.
        if not ready and idx < n and arrivals[idx].arrival_time > current_time:
            # Server would idle; jump to next arrival.
            current_time = arrivals[idx].arrival_time

        while idx < n and arrivals[idx].arrival_time <= current_time:
            j = arrivals[idx]
            heapq.heappush(ready, (-j.priority, j.arrival_time, j.job_id, j.burst_time))
            idx += 1

        # Run the best ready job to completion (non-preemptive).
        neg_prio, arr, jid, burst = heapq.heappop(ready)
        start_time = current_time
        current_time += burst
        completion[jid] = current_time
        waiting[jid] = start_time - arr

    results = [
        (j.job_id, completion[j.job_id], waiting[j.job_id])
        for j in sorted(jobs, key=lambda x: x.job_id)
    ]
    avg_wait = sum(waiting.values()) / n
    return results, avg_wait


# ---------- Deterministic demo ----------
if __name__ == "__main__":
    jobs = [
        Job(job_id=1, arrival_time=0, burst_time=4, priority=2),
        Job(job_id=2, arrival_time=1, burst_time=3, priority=5),
        Job(job_id=3, arrival_time=2, burst_time=1, priority=5),
        Job(job_id=4, arrival_time=3, burst_time=2, priority=1),
        Job(job_id=5, arrival_time=4, burst_time=5, priority=5),
    ]

    results, avg = simulate_nonpreemptive_priority_queue(jobs)

    print(f"{'JobID':>5} {'Completion':>11} {'Waiting':>8}")
    for jid, comp, wait in results:
        print(f"{jid:>5} {comp:>11} {wait:>8}")

    print(f"\nAverage waiting time: {avg:.3f}")