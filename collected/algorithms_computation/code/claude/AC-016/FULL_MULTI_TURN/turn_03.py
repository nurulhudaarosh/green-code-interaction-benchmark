import heapq
import unittest
from typing import Dict, List, Tuple

Job = Tuple[int, float, float, int]  # (job_id, arrival, burst, priority)


def simulate_queue(jobs: List[Job], include_summary: bool = False):
    """
    Non-preemptive single-server priority queue simulation.
    Selection: larger priority, then earlier arrival, then smaller job ID.

    Default (include_summary=False) returns exactly the original 3-tuple:
        (results, avg_waiting, order)
    With include_summary=True returns a 4-tuple:
        (results, avg_waiting, order, operation_summary)

    Raises ValueError on duplicate IDs or negative burst times.
    """
    summary = {
        "jobs_sorted": 0,
        "heap_pushes": 0,
        "heap_pops": 0,
        "idle_jumps": 0,
        "max_heap_size": 0,
        "priority_ties": 0,
        "id_tiebreaks": 0,
        "total_operations": 0,
    }

    if not jobs:
        return ({}, 0.0, [], summary) if include_summary else ({}, 0.0, [])

    ids = [j[0] for j in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError("job IDs must be unique")
    if any(j[2] < 0 for j in jobs):
        raise ValueError("burst times must be non-negative")

    pending = sorted(jobs, key=lambda j: (j[1], j[0]))  # input not mutated
    n = len(pending)
    summary["jobs_sorted"] = n

    # Heap key (-priority, arrival, id) is a total order -> deterministic.
    heap: List[Tuple[int, float, int, float]] = []
    results: Dict[int, Dict[str, float]] = {}
    order: List[int] = []

    t = pending[0][1]
    i = 0
    done = 0
    total_wait = 0

    while done < n:
        # Admit every job that has arrived by time t (arrival == t counts).
        while i < n and pending[i][1] <= t:
            jid, arr, burst, prio = pending[i]
            heapq.heappush(heap, (-prio, arr, jid, burst))
            summary["heap_pushes"] += 1
            i += 1
        if len(heap) > summary["max_heap_size"]:
            summary["max_heap_size"] = len(heap)

        if not heap:
            t = pending[i][1]  # idle: jump to next arrival
            summary["idle_jumps"] += 1
            continue

        neg_prio, arr, jid, burst = heapq.heappop(heap)
        summary["heap_pops"] += 1

        # O(1) peek at the runner-up to record how much tie-breaking was needed.
        if heap and heap[0][0] == neg_prio:
            summary["priority_ties"] += 1
            if heap[0][1] == arr:
                summary["id_tiebreaks"] += 1

        start = t
        completion = start + burst
        waiting = start - arr

        results[jid] = {"completion": completion, "waiting": waiting}
        order.append(jid)
        total_wait += waiting
        t = completion
        done += 1

    avg = total_wait / n
    if not include_summary:
        return results, avg, order

    summary["total_operations"] = (
        summary["heap_pushes"] + summary["heap_pops"] + summary["idle_jumps"]
    )
    return results, avg, order, summary


class TestOperationSummary(unittest.TestCase):
    SAMPLE = [(1, 0, 5, 1), (2, 1, 3, 3), (3, 2, 2, 3), (4, 2, 4, 2), (5, 20, 1, 1)]
    TIES = [(2, 0, 1, 1), (1, 0, 1, 1), (3, 0, 1, 2), (5, 1, 1, 1), (4, 1, 1, 1)]

    def test_default_return_shape_unchanged(self):
        out = simulate_queue(self.SAMPLE)
        self.assertEqual(len(out), 3)
        res, avg, order = out
        self.assertEqual(order, [1, 2, 3, 4, 5])
        self.assertAlmostEqual(avg, 3.6)
        self.assertEqual(res[5], {"completion": 21, "waiting": 0})

    def test_explicit_false_same_as_default(self):
        self.assertEqual(simulate_queue(self.SAMPLE, include_summary=False),
                         simulate_queue(self.SAMPLE))

    def test_summary_does_not_change_original_fields(self):
        for jobs in (self.SAMPLE, self.TIES):
            self.assertEqual(simulate_queue(jobs, include_summary=True)[:3],
                             simulate_queue(jobs))

    def test_summary_sample(self):
        s = simulate_queue(self.SAMPLE, include_summary=True)[3]
        self.assertEqual(s, {
            "jobs_sorted": 5, "heap_pushes": 5, "heap_pops": 5,
            "idle_jumps": 1, "max_heap_size": 3,
            "priority_ties": 1, "id_tiebreaks": 0, "total_operations": 11,
        })

    def test_summary_tie_levels(self):
        res, avg, order, s = simulate_queue(self.TIES, include_summary=True)
        self.assertEqual(order, [3, 1, 2, 4, 5])
        self.assertAlmostEqual(avg, 1.6)
        self.assertEqual(s["priority_ties"], 3)
        self.assertEqual(s["id_tiebreaks"], 2)
        self.assertEqual(s["max_heap_size"], 4)
        self.assertEqual(s["total_operations"], 10)

    def test_summary_empty(self):
        res, avg, order, s = simulate_queue([], include_summary=True)
        self.assertEqual((res, avg, order), ({}, 0.0, []))
        self.assertEqual(s["total_operations"], 0)
        self.assertEqual(simulate_queue([]), ({}, 0.0, []))

    def test_summary_is_deterministic(self):
        a = simulate_queue(self.TIES, include_summary=True)
        b = simulate_queue(list(reversed(self.TIES)), include_summary=True)
        self.assertEqual(a, b)  # input order does not matter

    def test_pops_equal_n_and_pushes_equal_n(self):
        n = 5000
        jobs = [(i, 0, 1, i) for i in range(1, n + 1)]
        s = simulate_queue(jobs, include_summary=True)[3]
        self.assertEqual((s["heap_pushes"], s["heap_pops"], s["max_heap_size"]), (n, n, n))

    def test_validation_unchanged(self):
        with self.assertRaises(ValueError):
            simulate_queue([(1, 0, 2, 1), (1, 0, 3, 1)], include_summary=True)
        with self.assertRaises(ValueError):
            simulate_queue([(1, 0, -1, 1)], include_summary=True)


if __name__ == "__main__":
    res, avg, order, ops = simulate_queue(TestOperationSummary.SAMPLE, include_summary=True)
    print("Order:", order, "Average waiting:", avg)
    print("operation_summary:", ops)
    unittest.main()