import heapq
from dataclasses import dataclass


@dataclass
class Job:
    job_id: int
    arrival: int
    service: int
    priority: int  # larger = higher priority


def simulate(jobs, include_operation_summary: bool = False):
    """
    Non-preemptive single-server priority-queue simulator.

    Selection rule: (-priority, arrival, job_id) — i.e. larger priority first,
    ties broken by earlier arrival, then smaller job_id.

    Returns
    -------
    dict
        {
          "results": {job_id: {"completion_time": int, "waiting_time": int}},
          "average_waiting_time": float,
          ["operation_summary": {...}]   # only if include_operation_summary=True
        }
    """
    jobs_sorted = sorted(jobs, key=lambda j: (j.arrival, j.job_id))

    heap = []                     # (-priority, arrival, job_id, service)
    idx = 0
    n = len(jobs_sorted)
    current_time = 0
    results = {}

    # --- counters for the optional operation_summary ---
    heap_pushes = 0
    heap_pops = 0
    idle_jumps = 0

    while idx < n or heap:
        # Server idle → jump clock to next arrival
        if not heap:
            current_time = max(current_time, jobs_sorted[idx].arrival)
            idle_jumps += 1

        # Enqueue every job that has arrived by current_time
        while idx < n and jobs_sorted[idx].arrival <= current_time:
            j = jobs_sorted[idx]
            heapq.heappush(heap, (-j.priority, j.arrival, j.job_id, j.service))
            heap_pushes += 1
            idx += 1

        # Dispatch the highest-priority job
        neg_priority, arrival, job_id, service = heapq.heappop(heap)
        heap_pops += 1

        start_time = current_time
        completion_time = start_time + service
        waiting_time = start_time - arrival

        results[job_id] = {
            "completion_time": completion_time,
            "waiting_time": waiting_time,
        }
        current_time = completion_time

    avg_wait = (
        sum(r["waiting_time"] for r in results.values()) / n if n else 0.0
    )

    output = {
        "results": results,
        "average_waiting_time": avg_wait,
    }

    if include_operation_summary:
        output["operation_summary"] = {
            "heap_pushes": heap_pushes,
            "heap_pops": heap_pops,
            "idle_jumps": idle_jumps,
            "total_operations": heap_pushes + heap_pops + idle_jumps,
        }

    return output


# ---------------- Deterministic demonstration ----------------
if __name__ == "__main__":
    jobs = [
        Job(1, 0, 5, 1),
        Job(2, 1, 3, 3),
        Job(3, 2, 2, 3),
        Job(4, 3, 4, 2),
        Job(5, 10, 1, 5),
    ]

    # --- Feature OFF: exactly the original outputs ---
    print("=== Feature OFF (original outputs only) ===")
    legacy = simulate(jobs)  # include_operation_summary defaults to False
    print(legacy)

    print()

    # --- Feature ON: original outputs preserved + operation_summary ---
    print("=== Feature ON (original outputs + operation_summary) ===")
    extended = simulate(jobs, include_operation_summary=True)
    print(extended)

    # Sanity check: original fields are identical in both modes
    assert extended["results"] == legacy["results"]
    assert extended["average_waiting_time"] == legacy["average_waiting_time"]
    print("\nBackwards-compatibility check: PASSED")