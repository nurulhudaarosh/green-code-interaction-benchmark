import heapq
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Job:
    job_id: int
    arrival_time: int
    burst_time: int
    priority: int

    def __post_init__(self):
        if self.job_id < 0:
            raise ValueError("job_id must be non-negative")
        if self.arrival_time < 0:
            raise ValueError("arrival_time must be non-negative")
        if self.burst_time <= 0:
            raise ValueError("burst_time must be positive")


def simulate_queue(jobs: List[Job]) -> Tuple[List[Tuple[int, int, int]], float]:
    """
    Non-preemptive single-server priority queue simulation.

    Returns:
        results: list of (job_id, completion_time, waiting_time), sorted by job_id
        avg_waiting_time: float
    """
    if not jobs:
        return [], 0.0

    # Order arrivals for streaming into the ready heap.
    arrivals = sorted(jobs, key=lambda j: (j.arrival_time, j.job_id))

    ready = []  # heap of (-priority, arrival_time, job_id, burst_time)
    current_time = 0
    idx = 0
    results = []
    total_wait = 0

    while idx < len(arrivals) or ready:
        # Admit all jobs that have arrived by now.
        while idx < len(arrivals) and arrivals[idx].arrival_time <= current_time:
            j = arrivals[idx]
            heapq.heappush(ready, (-j.priority, j.arrival_time, j.job_id, j.burst_time))
            idx += 1

        # Idle: jump ahead to the next arrival.
        if not ready:
            current_time = arrivals[idx].arrival_time
            continue

        # Pick and run the best job to completion (non-preemptive).
        neg_prio, arr, jid, burst = heapq.heappop(ready)
        start = current_time
        completion = start + burst
        waiting = start - arr

        results.append((jid, completion, waiting))
        total_wait += waiting
        current_time = completion

    results.sort(key=lambda x: x[0])  # report by job_id
    return results, total_wait / len(jobs)


def print_results(jobs: List[Job], results, avg_wait: float) -> None:
    meta = {j.job_id: j for j in jobs}
    print(f"{'ID':<4}{'Arr':<6}{'Burst':<7}{'Prio':<6}{'Comp':<7}{'Wait':<7}")
    print("-" * 37)
    for jid, comp, wait in results:
        j = meta[jid]
        print(f"{jid:<4}{j.arrival_time:<6}{j.burst_time:<7}"
              f"{j.priority:<6}{comp:<7}{wait:<7}")
    print("-" * 37)
    print(f"Average waiting time: {avg_wait:.2f}")


def run_tests() -> None:
    cases = {
        "Basic priority scheduling": [
            Job(1, 0, 5, 1),
            Job(2, 1, 3, 3),
            Job(3, 2, 2, 2),
            Job(4, 4, 4, 4),
        ],
        "Same priority - tie by arrival then ID": [
            Job(3, 0, 2, 5),
            Job(1, 0, 3, 5),
            Job(2, 1, 4, 5),
        ],
        "Idle gaps between arrivals": [
            Job(1, 0, 2, 1),
            Job(2, 10, 3, 2),
            Job(3, 15, 1, 3),
        ],
        "High priority arrives mid-execution (non-preemptive)": [
            Job(1, 0, 10, 1),
            Job(2, 2, 2, 5),
            Job(3, 3, 1, 3),
        ],
        "All arrive at t=0": [
            Job(1, 0, 4, 2),
            Job(2, 0, 3, 5),
            Job(3, 0, 2, 5),
            Job(4, 0, 1, 1),
        ],
    }

    for title, jobs in cases.items():
        print("=" * 37)
        print(title)
        print("=" * 37)
        results, avg = simulate_queue(jobs)
        print_results(jobs, results, avg)
        print()


if __name__ == "__main__":
    run_tests()