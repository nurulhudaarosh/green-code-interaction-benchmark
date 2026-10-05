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


def _empty_summary() -> Dict[str, int]:
    return {
        "jobs_sorted": 0,
        "heap_pushes": 0,
        "heap_pops": 0,
        "idle_jumps": 0,
        "contested_decisions": 0,
        "total_major_operations": 0,
    }


def simulate(jobs: List[Job], include_summary: bool = False):
    """
    Simulate a non-preemptive single-server priority queue.

    include_summary=False (default):
        returns (results, avg_wait)  -- identical to the original behavior.
    include_summary=True:
        returns (results, avg_wait, operation_summary).

    results: {job_id: {"completion": ..., "waiting": ...}}
    avg_wait: average waiting time (0.0 if there are no jobs)
    """
    ops = _empty_summary()

    if not jobs:
        return ({}, 0.0, ops) if include_summary else ({}, 0.0)

    ids = [j.id for j in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError("Job IDs must be unique")
    for j in jobs:
        if j.arrival < 0 or j.burst < 0:
            raise ValueError(f"Job {j.id}: arrival and burst must be non-negative")

    pending = sorted(jobs, key=lambda j: (j.arrival, j.id))
    ops["jobs_sorted"] = len(pending)
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
            ops["idle_jumps"] += 1

        # Admit every job that has arrived by time t.
        while i < n and pending[i].arrival <= t:
            j = pending[i]
            heapq.heappush(heap, (-j.priority, j.arrival, j.id, j))
            ops["heap_pushes"] += 1
            i += 1

        # Serve the best waiting job to completion.
        if len(heap) > 1:
            ops["contested_decisions"] += 1
        _, _, _, job = heapq.heappop(heap)
        ops["heap_pops"] += 1

        start = t
        completion = start + job.burst
        wait = start - job.arrival
        results[job.id] = {"completion": completion, "waiting": wait}
        total_wait += wait
        t = completion
        done += 1

    ops["total_major_operations"] = (
        ops["heap_pushes"] + ops["heap_pops"] + ops["idle_jumps"]
    )
    avg_wait = total_wait / n

    if include_summary:
        return results, avg_wait, ops
    return results, avg_wait


def main() -> None:
    jobs = [
        Job(id=1, arrival=0, burst=5, priority=1),
        Job(id=2, arrival=1, burst=3, priority=3),
        Job(id=3, arrival=2, burst=2, priority=3),
        Job(id=4, arrival=2, burst=4, priority=5),
        Job(id=5, arrival=20, burst=1, priority=1),
    ]

    # Feature disabled: original output, unchanged.
    results, avg = simulate(jobs)
    for jid in sorted(results):
        r = results[jid]
        print(f"Job {jid}: completion={r['completion']}, waiting={r['waiting']}")
    print(f"Average waiting time: {avg:.4f}")

    # Feature enabled.
    results2, avg2, summary = simulate(jobs, include_summary=True)
    assert results2 == results and avg2 == avg  # original fields identical
    print("operation_summary:", summary)


if __name__ == "__main__":
    main()