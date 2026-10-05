import heapq
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

Number = Union[int, float]


@dataclass(frozen=True)
class Job:
    id: int
    arrival: Number
    burst: Number
    priority: Number


def simulate(jobs: List[Job]) -> Tuple[Dict[int, Dict[str, Number]], float]:
    """
    Simulate a non-preemptive single-server priority queue.

    Returns:
        results: {job_id: {"completion": ..., "waiting": ...}}
        avg_wait: average waiting time (0.0 if there are no jobs)
    """
    if not jobs:
        return {}, 0.0

    ids = [j.id for j in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError("Job IDs must be unique")
    for j in jobs:
        if j.arrival < 0 or j.burst < 0:
            raise ValueError(f"Job {j.id}: arrival and burst must be non-negative")

    pending = sorted(jobs, key=lambda j: (j.arrival, j.id))
    n = len(pending)
    heap: List[Tuple[Number, Number, int, Job]] = []
    results: Dict[int, Dict[str, Number]] = {}

    t: Number = 0
    i = 0
    done = 0
    total_wait: Number = 0

    while done < n:
        # Idle: jump to the next arrival.
        if not heap and i < n and pending[i].arrival > t:
            t = pending[i].arrival

        # Admit every job that has arrived by time t.
        while i < n and pending[i].arrival <= t:
            j = pending[i]
            heapq.heappush(heap, (-j.priority, j.arrival, j.id, j))
            i += 1

        # Serve the best waiting job to completion.
        _, _, _, job = heapq.heappop(heap)
        start = t
        completion = start + job.burst
        wait = start - job.arrival
        results[job.id] = {"completion": completion, "waiting": wait}
        total_wait += wait
        t = completion
        done += 1

    return results, total_wait / n


def main() -> None:
    jobs = [
        Job(id=1, arrival=0, burst=5, priority=1),
        Job(id=2, arrival=1, burst=3, priority=3),
        Job(id=3, arrival=2, burst=2, priority=3),
        Job(id=4, arrival=2, burst=4, priority=5),
        Job(id=5, arrival=20, burst=1, priority=1),
    ]
    results, avg = simulate(jobs)
    for jid in sorted(results):
        r = results[jid]
        print(f"Job {jid}: completion={r['completion']}, waiting={r['waiting']}")
    print(f"Average waiting time: {avg:.4f}")


if __name__ == "__main__":
    main()