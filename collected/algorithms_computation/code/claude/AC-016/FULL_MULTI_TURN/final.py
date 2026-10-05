import heapq
import unittest
from typing import Dict, List, Tuple

Job = Tuple[int, float, float, int]  # (job_id, arrival, burst, priority)


def simulate_queue(jobs: List[Job], include_summary: bool = False):
    """
    Non-preemptive single-server priority queue simulation.
    Selection: larger priority, then earlier arrival, then smaller job ID.

    Default returns the original 3-tuple: (results, avg_waiting, order).
    With include_summary=True returns (results, avg_waiting, order, operation_summary).
    Raises ValueError on duplicate IDs or negative burst times.
    """
    summary = {
        "jobs_sorted": 0, "heap_pushes": 0, "heap_pops": 0, "idle_jumps": 0,
        "max_heap_size": 0, "priority_ties": 0, "id_tiebreaks": 0,
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

    # Key (-priority, arrival, id) is a total order (IDs unique) -> deterministic.
    heap: List[Tuple[int, float, int, float]] = []
    results: Dict[int, Dict[str, float]] = {}
    order: List[int] = []

    t = pending[0][1]
    i = 0
    done = 0
    total_wait = 0

    while done < n:
        while i < n and pending[i][1] <= t:  # arrival == t is eligible
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

        if heap and heap[0][0] == neg_prio:  # O(1) peek at runner-up
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


def brute_force(jobs: List[Job]):
    """O(n^2) reference implementing the same three-level rule directly."""
    remaining = list(jobs)
    t = 0
    results, order, total = {}, [], 0
    while remaining:
        avail = [j for j in remaining if j[1] <= t]
        if not avail:
            t = min(j[1] for j in remaining)
            continue
        best = min(avail, key=lambda j: (-j[3], j[1], j[0]))
        remaining.remove(best)
        jid, arr, burst, _ = best
        results[jid] = {"completion": t + burst, "waiting": t - arr}
        order.append(jid)
        total += t - arr
        t += burst
    n = len(jobs)
    return results, (total / n if n else 0.0), order


class TestOriginalBehavior(unittest.TestCase):
    SAMPLE = [(1, 0, 5, 1), (2, 1, 3, 3), (3, 2, 2, 3), (4, 2, 4, 2), (5, 20, 1, 1)]

    def test_empty(self):
        self.assertEqual(simulate_queue([]), ({}, 0.0, []))

    def test_original_sample_and_shape(self):
        out = simulate_queue(self.SAMPLE)
        self.assertEqual(len(out), 3)
        res, avg, order = out
        self.assertEqual(order, [1, 2, 3, 4, 5])
        self.assertEqual(res[2], {"completion": 8, "waiting": 4})
        self.assertEqual(res[5], {"completion": 21, "waiting": 0})
        self.assertAlmostEqual(avg, 3.6)

    def test_three_level_ties(self):
        jobs = [(2, 0, 1, 1), (1, 0, 1, 1), (3, 0, 1, 2), (5, 1, 1, 1), (4, 1, 1, 1)]
        res, avg, order = simulate_queue(jobs)
        self.assertEqual(order, [3, 1, 2, 4, 5])
        self.assertEqual([res[k]["waiting"] for k in (3, 1, 2, 4, 5)], [0, 1, 2, 2, 3])
        self.assertAlmostEqual(avg, 1.6)

    def test_boundaries(self):
        # arrival exactly at completion is eligible and wins on priority
        _, _, order = simulate_queue([(1, 0, 5, 1), (2, 5, 1, 9), (3, 1, 1, 5)])
        self.assertEqual(order, [1, 2, 3])
        # idle gap and zero burst
        res, avg, order = simulate_queue([(1, 10, 2, 1), (2, 0, 3, 1)])
        self.assertEqual((order, avg, res[1]["completion"]), ([2, 1], 0.0, 12))
        res, _, order = simulate_queue([(2, 0, 0, 1), (1, 0, 0, 1)])
        self.assertEqual(order, [1, 2])

    def test_validation(self):
        with self.assertRaises(ValueError):
            simulate_queue([(1, 0, 2, 1), (1, 0, 3, 1)])
        with self.assertRaises(ValueError):
            simulate_queue([(1, 0, -1, 1)])

    def test_input_not_mutated(self):
        jobs = [(2, 5, 1, 1), (1, 0, 1, 1)]
        snap = list(jobs)
        simulate_queue(jobs)
        self.assertEqual(jobs, snap)


class TestWorstCaseStructures(unittest.TestCase):
    N = 100_000

    def test_max_heap_all_at_zero_ascending_priority(self):
        n = self.N
        jobs = [(i, 0, 1, i) for i in range(1, n + 1)]
        res, avg, order, s = simulate_queue(jobs, include_summary=True)
        self.assertEqual(order, list(range(n, 0, -1)))
        for k in (1, 2, n // 2, n - 1, n):
            self.assertEqual(res[k], {"completion": n - k + 1, "waiting": n - k})
        self.assertAlmostEqual(avg, (n - 1) / 2)
        self.assertEqual(s, {
            "jobs_sorted": n, "heap_pushes": n, "heap_pops": n, "idle_jumps": 0,
            "max_heap_size": n, "priority_ties": 0, "id_tiebreaks": 0,
            "total_operations": 2 * n,
        })

    def test_long_blocker_heap_fills_then_drains(self):
        n = self.N
        blocker = n + 5
        jobs = [(0, 0, blocker, 0)] + [(i, i, 1, i) for i in range(1, n + 1)]
        res, _, order, s = simulate_queue(jobs, include_summary=True)
        self.assertEqual(order, [0] + list(range(n, 0, -1)))
        self.assertEqual(res[0], {"completion": blocker, "waiting": 0})
        for i in (1, 7, n // 2, n):
            start = blocker + (n - i)
            self.assertEqual(res[i], {"completion": start + 1, "waiting": start - i})
        self.assertEqual(s["max_heap_size"], n)
        self.assertEqual((s["heap_pushes"], s["heap_pops"]), (n + 1, n + 1))
        self.assertEqual((s["idle_jumps"], s["priority_ties"]), (0, 0))
        self.assertEqual(s["total_operations"], 2 * (n + 1))

    def test_full_tiebreak_chain_descending_ids(self):
        n = 50_000
        jobs = [(i, 0, 1, 5) for i in range(n, 0, -1)]
        res, avg, order, s = simulate_queue(jobs, include_summary=True)
        self.assertEqual(order, list(range(1, n + 1)))
        self.assertEqual(res[n], {"completion": n, "waiting": n - 1})
        self.assertAlmostEqual(avg, (n - 1) / 2)
        self.assertEqual(s["priority_ties"], n - 1)
        self.assertEqual(s["id_tiebreaks"], n - 1)
        self.assertEqual(s["max_heap_size"], n)

    def test_max_idle_jumps(self):
        n = self.N
        jobs = [(i, 10 * i, 1, 1) for i in range(n, 0, -1)]  # reversed input
        res, avg, order, s = simulate_queue(jobs, include_summary=True)
        self.assertEqual(order, list(range(1, n + 1)))
        self.assertEqual(res[n], {"completion": 10 * n + 1, "waiting": 0})
        self.assertEqual(avg, 0.0)
        self.assertEqual(s["idle_jumps"], n - 1)
        self.assertEqual(s["max_heap_size"], 1)
        self.assertEqual(s["total_operations"], 3 * n - 1)

    def test_summary_does_not_alter_original_fields(self):
        n = 20_000
        jobs = [(i, 0, 1, i) for i in range(1, n + 1)]
        self.assertEqual(simulate_queue(jobs, include_summary=True)[:3],
                         simulate_queue(jobs))

    def test_deterministic_regardless_of_input_order(self):
        n = 5_000
        jobs = [(i, i % 7, 1 + i % 3, i % 4) for i in range(1, n + 1)]
        a = simulate_queue(jobs, include_summary=True)
        b = simulate_queue(list(reversed(jobs)), include_summary=True)
        self.assertEqual(a, b)

    def test_matches_brute_force_heavy_ties(self):
        state = 12345  # deterministic LCG, no random module

        def rnd(m):
            nonlocal state
            state = (state * 1103515245 + 12345) % (2 ** 31)
            return state % m

        for _ in range(300):
            n = 1 + rnd(30)
            jobs = [(i, rnd(25), rnd(6), rnd(4)) for i in range(1, n + 1)]
            self.assertEqual(simulate_queue(jobs), brute_force(jobs))


if __name__ == "__main__":
    unittest.main()