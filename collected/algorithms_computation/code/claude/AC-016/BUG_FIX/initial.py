"""
PROBLEM
-------
Simulate a non-preemptive single-server queue.
Each job has: id, arrival time, service (burst) time, priority.
Whenever the server becomes free, it picks among jobs that have already
arrived the one with:
    1. the LARGER priority first,
    2. ties -> EARLIER arrival time,
    3. ties -> SMALLER job id.
A started job runs to completion (non-preemptive).
If no job is available, the server idles until the next arrival.

KEY CONSTRAINTS
---------------
- Single server, non-preemptive.
- Selection is made only among jobs with arrival <= current time.
- Deterministic tie-breaking as above.
- Standard library only; no network, randomness, or user interaction.

REQUIRED OUTPUT
---------------
- For every job: completion time and waiting time
  (waiting = start - arrival; completion = start + service).
- The average waiting time over all jobs.

ALGORITHM
---------
1. Sort jobs by (arrival, id).
2. Keep a clock `time` and an index `i` into the sorted list.
3. Push every job with arrival <= time into a min-heap keyed by
   (-priority, arrival, id).
4. If the heap is empty, jump the clock to the next arrival.
   Otherwise pop the best job, start it at `time`, record waiting and
   completion, and advance the clock by its service time.
5. Repeat until all jobs are done. Complexity: O(n log n).
"""

import heapq
from typing import Dict, List, Tuple


def simulate(jobs: List[Tuple[int, int, int, int]]):
    """
    jobs: list of (job_id, arrival, service, priority)
    Returns: (results, average_waiting)
      results: dict job_id -> (completion_time, waiting_time)
    """
    if not jobs:
        return {}, 0.0

    order = sorted(jobs, key=lambda j: (j[1], j[0]))  # by arrival, then id
    n = len(order)
    heap: List[Tuple[int, int, int, int]] = []  # (-priority, arrival, id, service)
    results: Dict[int, Tuple[int, int]] = {}

    time = 0
    i = 0
    done = 0
    total_wait = 0

    while done < n:
        # Admit all jobs that have arrived by the current time
        while i < n and order[i][1] <= time:
            jid, arr, svc, pr = order[i]
            heapq.heappush(heap, (-pr, arr, jid, svc))
            i += 1

        if not heap:
            # Server idle: jump to the next arrival
            time = order[i][1]
            continue

        neg_pr, arr, jid, svc = heapq.heappop(heap)
        start = time
        wait = start - arr
        completion = start + svc
        results[jid] = (completion, wait)
        total_wait += wait
        time = completion
        done += 1

    return results, total_wait / n


def main():
    # (job_id, arrival, service, priority)
    jobs = [
        (1, 0, 5, 1),
        (2, 1, 3, 3),
        (3, 2, 2, 3),
        (4, 3, 4, 2),
        (5, 20, 2, 1),
        (6, 20, 1, 1),
    ]

    results, avg_wait = simulate(jobs)

    print("Job  Completion  Waiting")
    for jid in sorted(results):
        c, w = results[jid]
        print(f"{jid:>3}  {c:>10}  {w:>7}")
    print(f"Average waiting time: {avg_wait:.4f}")


if __name__ == "__main__":
    main()