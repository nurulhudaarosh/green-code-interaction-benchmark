import heapq
from typing import Dict, List, Tuple

Job = Tuple[int, int, int, int]  # (job_id, arrival, service, priority)


def _validate(jobs: List[Job]) -> None:
    seen = set()
    for job in jobs:
        if len(job) != 4:
            raise ValueError(f"Job must be (id, arrival, service, priority): {job}")
        jid, arr, svc, _pr = job
        if jid in seen:
            raise ValueError(f"Duplicate job id: {jid}")  # FIX: was silently overwritten
        seen.add(jid)
        if arr < 0 or svc < 0:
            raise ValueError(f"Arrival and service must be >= 0: {job}")


def simulate(jobs: List[Job]) -> Tuple[Dict[int, Tuple[int, int]], float]:
    """Returns ({job_id: (completion, waiting)}, average_waiting)."""
    _validate(jobs)
    if not jobs:
        return {}, 0.0

    order = sorted(jobs, key=lambda j: (j[1], j[0]))  # arrival, then id
    n = len(order)
    heap: List[Tuple[int, int, int, int]] = []        # (-priority, arrival, id, service)
    results: Dict[int, Tuple[int, int]] = {}

    time = 0
    i = 0
    total_wait = 0

    while len(results) < n:
        while i < n and order[i][1] <= time:          # admit arrived jobs
            jid, arr, svc, pr = order[i]
            heapq.heappush(heap, (-pr, arr, jid, svc))
            i += 1

        if not heap:                                  # idle: jump to next arrival
            time = order[i][1]
            continue

        _neg_pr, arr, jid, svc = heapq.heappop(heap)
        wait = time - arr
        time += svc
        results[jid] = (time, wait)
        total_wait += wait

    return results, total_wait / n


def _reference(jobs: List[Job]):
    """Independent O(n^2) simulator used only to verify simulate()."""
    pending = list(jobs)
    time, out = 0, {}
    while pending:
        ready = [j for j in pending if j[1] <= time]
        if not ready:
            time = min(j[1] for j in pending)
            continue
        best = min(ready, key=lambda j: (-j[3], j[1], j[0]))
        pending.remove(best)
        out[best[0]] = (time + best[2], time - best[1])
        time += best[2]
    return out


def main():
    # Defect demo 1: duplicate ids used to give 1 result but average over 2 jobs.
    try:
        simulate([(1, 0, 2, 1), (1, 0, 3, 1)])
    except ValueError as e:
        print("Duplicate-id input now rejected:", e)

    # Defect demo 2: the previously printed sample output was wrong.
    jobs = [
        (1, 0, 5, 1),
        (2, 1, 3, 3),
        (3, 2, 2, 3),
        (4, 3, 4, 2),
        (5, 20, 2, 1),
        (6, 20, 1, 1),
    ]
    results, avg = simulate(jobs)
    assert results == _reference(jobs)
    assert results == {1: (5, 0), 2: (8, 4), 3: (10, 6),
                       4: (14, 7), 5: (22, 0), 6: (23, 2)}

    # Deterministic cross-check (LCG, no randomness) with ties and idle gaps.
    seed = 12345
    for _ in range(200):
        gen = []
        for jid in range(1, 9):
            seed = (seed * 1103515245 + 12345) % (2 ** 31)
            arr = seed % 15
            seed = (seed * 1103515245 + 12345) % (2 ** 31)
            svc = seed % 6
            seed = (seed * 1103515245 + 12345) % (2 ** 31)
            gen.append((jid, arr, svc, seed % 3))
        assert simulate(gen)[0] == _reference(gen)

    print("\nJob  Completion  Waiting")
    for jid in sorted(results):
        c, w = results[jid]
        print(f"{jid:>3}  {c:>10}  {w:>7}")
    print(f"Average waiting time: {avg:.4f}")


if __name__ == "__main__":
    main()