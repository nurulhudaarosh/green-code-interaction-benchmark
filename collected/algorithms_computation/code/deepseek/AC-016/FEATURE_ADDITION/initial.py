import heapq
from dataclasses import dataclass


@dataclass
class Job:
    job_id: int
    arrival: int
    service: int
    priority: int  # larger = higher priority


def simulate(jobs):
    """
    Simulate a non-preemptive single-server priority queue.

    Selection rule: highest priority first; ties broken by
    earlier arrival, then smaller job_id.

    Returns:
        results: dict job_id -> (completion_time, waiting_time)
        avg_wait: average waiting time across all jobs
    """
    # Sort jobs by arrival for streaming into the ready queue
    jobs_sorted = sorted(jobs, key=lambda j: (j.arrival, j.job_id))

    # Heap entries: (-priority, arrival, job_id, service)
    heap = []
    n = len(jobs_sorted)
    idx = 0
    current_time = 0
    results = {}

    while idx < n or heap:
        # If heap empty, jump time to next arrival
        if not heap:
            current_time = max(current_time, jobs_sorted[idx].arrival)

        # Add all jobs that have arrived by current_time
        while idx < n and jobs_sorted[idx].arrival <= current_time:
            j = jobs_sorted[idx]
            heapq.heappush(heap, (-j.priority, j.arrival, j.job_id, j.service))
            idx += 1

        # Pop the highest-priority job
        neg_priority, arrival, job_id, service = heapq.heappop(heap)

        start_time = current_time
        completion_time = start_time + service
        waiting_time = start_time - arrival

        results[job_id] = (completion_time, waiting_time)
        current_time = completion_time

    avg_wait = sum(w for _, w in results.values()) / n if n else 0.0
    return results, avg_wait


# ---- Deterministic test / demonstration ----
if __name__ == "__main__":
    # Example jobs: (id, arrival, service, priority)
    jobs = [
        Job(1, 0, 5, 1),
        Job(2, 1, 3, 3),
        Job(3, 2, 2, 3),
        Job(4, 3, 4, 2),
        Job(5, 10, 1, 5),
    ]

    results, avg_wait = simulate(jobs)

    print("Job | Completion | Waiting")
    print("----+------------+--------")
    for job_id in sorted(results):
        comp, wait = results[job_id]
        print(f"{job_id:>3} | {comp:>10} | {wait:>7}")

    print(f"\nAverage waiting time: {avg_wait:.3f}")