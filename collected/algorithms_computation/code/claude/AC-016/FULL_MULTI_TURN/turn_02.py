import heapq
import unittest
from typing import Dict, List, Tuple

Job = Tuple[int, float, float, int]  # (job_id, arrival, burst, priority)


def simulate_queue(jobs: List[Job]):
    """
    Non-preemptive single-server priority queue simulation.
    Selection: larger priority, then earlier arrival, then smaller job ID.

    Returns (results, avg_waiting, order):
        results: {job_id: {"completion": ..., "waiting": ...}}
        avg_waiting: float (0.0 if there are no jobs)
        order: job IDs in execution order
    Raises ValueError on duplicate IDs or negative burst times.
    """
    if not jobs:
        return {}, 0.0, []

    ids = [j[0] for j in jobs]
    if len(set(ids)) != len(ids):
        raise ValueError("job IDs must be unique")
    if any(j[2] < 0 for j in jobs):
        raise ValueError("burst times must be non-negative")

    pending = sorted(jobs, key=lambda j: (j[1], j[0]))  # input not mutated
    n = len(pending)

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
            i += 1

        if not heap:
            t = pending[i][1]  # idle: jump to next arrival
            continue

        _, arr, jid, burst = heapq.heappop(heap)
        start = t
        completion = start + burst
        waiting = start - arr

        results[jid] = {"completion": completion, "waiting": waiting}
        order.append(jid)
        total_wait += waiting
        t = completion
        done += 1

    return results, total_wait / n, order


def brute_force(jobs: List[Job]):
    """O(n^2) reference implementing the same rules directly."""
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


class TestSimulator(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(simulate_queue([]), ({}, 0.0, []))

    def test_original_sample(self):
        sample = [(1, 0, 5, 1), (2, 1, 3, 3), (3, 2, 2, 3),
                  (4, 2, 4, 2), (5, 20, 1, 1)]
        res, avg, order = simulate_queue(sample)
        self.assertEqual(order, [1, 2, 3, 4, 5])
        self.assertEqual(res[2], {"completion": 8, "waiting": 4})
        self.assertEqual(res[3], {"completion": 10, "waiting": 6})
        self.assertEqual(res[4], {"completion": 14, "waiting": 8})
        self.assertEqual(res[5], {"completion": 21, "waiting": 0})
        self.assertAlmostEqual(avg, 3.6)

    def test_three_level_ties(self):
        jobs = [(2, 0, 1, 1), (1, 0, 1, 1), (3, 0, 1, 2), (5, 1, 1, 1), (4, 1, 1, 1)]
        res, avg, order = simulate_queue(jobs)
        self.assertEqual(order, [3, 1, 2, 4, 5])
        self.assertEqual([res[k]["waiting"] for k in (3, 1, 2, 4, 5)], [0, 1, 2, 2, 3])
        self.assertAlmostEqual(avg, 1.6)

    def test_arrival_exactly_at_completion(self):
        jobs = [(1, 0, 5, 1), (2, 5, 1, 9), (3, 1, 1, 5)]
        res, avg, order = simulate_queue(jobs)
        self.assertEqual(order, [1, 2, 3])
        self.assertEqual(res[2], {"completion": 6, "waiting": 0})
        self.assertEqual(res[3], {"completion": 7, "waiting": 5})
        self.assertAlmostEqual(avg, 5 / 3)

    def test_idle_gap(self):
        res, avg, order = simulate_queue([(1, 10, 2, 1), (2, 0, 3, 1)])
        self.assertEqual(order, [2, 1])
        self.assertEqual(res[1], {"completion": 12, "waiting": 0})
        self.assertEqual(avg, 0.0)

    def test_zero_burst(self):
        res, _, order = simulate_queue([(2, 0, 0, 1), (1, 0, 0, 1)])
        self.assertEqual(order, [1, 2])
        self.assertEqual(res[1], {"completion": 0, "waiting": 0})

    def test_priority_beats_arrival(self):
        _, _, order = simulate_queue([(1, 0, 10, 0), (2, 1, 1, 1), (3, 2, 1, 9)])
        self.assertEqual(order, [1, 3, 2])

    def test_tie_arrival_then_id(self):
        jobs = [(1, 0, 10, 0), (5, 3, 1, 2), (4, 3, 1, 2), (6, 2, 1, 2)]
        res, _, order = simulate_queue(jobs)
        self.assertEqual(order, [1, 6, 4, 5])
        self.assertEqual(res[4], {"completion": 12, "waiting": 8})

    def test_all_equal_except_id_descending_input(self):
        n = 1000
        jobs = [(i, 0, 1, 5) for i in range(n, 0, -1)]
        res, avg, order = simulate_queue(jobs)
        self.assertEqual(order, list(range(1, n + 1)))
        self.assertEqual(res[n], {"completion": n, "waiting": n - 1})
        self.assertAlmostEqual(avg, (n - 1) / 2)

    def test_worst_case_heap_all_at_zero(self):
        n = 100_000
        jobs = [(i, 0, 1, i) for i in range(1, n + 1)]
        res, avg, order = simulate_queue(jobs)
        self.assertEqual(order, list(range(n, 0, -1)))
        for k in (1, 2, n // 2, n - 1, n):
            self.assertEqual(res[k], {"completion": n - k + 1, "waiting": n - k})
        self.assertAlmostEqual(avg, (n - 1) / 2)

    def test_worst_case_long_blocker(self):
        n = 100_000
        blocker = n + 5
        jobs = [(0, 0, blocker, 0)] + [(i, i, 1, i) for i in range(1, n + 1)]
        res, _, order = simulate_queue(jobs)
        self.assertEqual(order, [0] + list(range(n, 0, -1)))
        for i in (1, 7, n // 2, n):
            start = blocker + (n - i)
            self.assertEqual(res[i], {"completion": start + 1, "waiting": start - i})

    def test_matches_brute_force(self):
        state = 12345  # deterministic LCG, no randomness module

        def rnd(m):
            nonlocal state
            state = (state * 1103515245 + 12345) % (2 ** 31)
            return state % m

        for _ in range(300):
            n = 1 + rnd(30)
            jobs = [(i, rnd(25), rnd(6), rnd(4)) for i in range(1, n + 1)]
            self.assertEqual(simulate_queue(jobs), brute_force(jobs))

    def test_input_not_mutated(self):
        jobs = [(2, 5, 1, 1), (1, 0, 1, 1)]
        snapshot = list(jobs)
        simulate_queue(jobs)
        self.assertEqual(jobs, snapshot)

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            simulate_queue([(1, 0, 2, 1), (1, 0, 3, 1)])

    def test_negative_burst_rejected(self):
        with self.assertRaises(ValueError):
            simulate_queue([(1, 0, -1, 1)])


if __name__ == "__main__":
    demo = [(2, 0, 1, 1), (1, 0, 1, 1), (3, 0, 1, 2), (5, 1, 1, 1), (4, 1, 1, 1)]
    res, avg, order = simulate_queue(demo)
    print("Order:", order, "Average waiting:", avg)  # [3, 1, 2, 4, 5] 1.6
    unittest.main()