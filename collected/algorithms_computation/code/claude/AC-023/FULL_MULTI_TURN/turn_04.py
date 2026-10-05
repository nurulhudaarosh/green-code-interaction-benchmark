import unittest

from threshold_connectivity import component_stats

BIG = 10**18


def brute_force(n, edges, queries):
    """Reference: rebuild labels from scratch for every query (O(k*m*n))."""
    out = []
    for q in queries:
        label = list(range(n))
        for u, v, w in edges:
            if w <= q and label[u] != label[v]:
                old, new = label[v], label[u]
                label = [new if x == old else x for x in label]
        counts = {}
        for x in label:
            counts[x] = counts.get(x, 0) + 1
        out.append((len(counts), max(counts.values()) if counts else 0))
    return out


class EmptyAndTinyInputs(unittest.TestCase):
    def test_n_zero(self):
        self.assertEqual(component_stats(0, [], [0, -5, BIG]), [(0, 0)] * 3)

    def test_n_zero_no_queries_with_summary(self):
        res = component_stats(0, [], [], include_summary=True)
        self.assertEqual(res["answers"], [])
        s = res["operation_summary"]
        self.assertEqual(s["total_major_operations"], 0)
        self.assertEqual(s["edges_processed"], 0)

    def test_n_one_no_edges(self):
        self.assertEqual(component_stats(1, [], [-1, 0, 7]), [(1, 1)] * 3)

    def test_n_one_self_loop(self):
        res = component_stats(1, [(0, 0, 3)], [2, 3, 4], include_summary=True)
        self.assertEqual(res["answers"], [(1, 1)] * 3)
        s = res["operation_summary"]
        self.assertEqual(s["unions_performed"], 0)
        self.assertEqual(s["redundant_edges_skipped"], 1)

    def test_no_queries(self):
        self.assertEqual(component_stats(3, [(0, 1, 1)], []), [])

    def test_no_edges(self):
        self.assertEqual(component_stats(5, [], [0, 9]), [(5, 1), (5, 1)])


class ThresholdBoundaries(unittest.TestCase):
    def test_below_equal_above_weight(self):
        self.assertEqual(
            component_stats(2, [(0, 1, 5)], [4, 5, 6]),
            [(2, 1), (1, 2), (1, 2)],
        )

    def test_extreme_weights_and_queries(self):
        edges = [(0, 1, -BIG), (1, 2, 0), (2, 3, BIG)]
        queries = [-BIG - 1, -BIG, -1, 0, BIG - 1, BIG, BIG + 1]
        self.assertEqual(
            component_stats(4, edges, queries),
            [(4, 1), (3, 2), (3, 2), (2, 3), (2, 3), (1, 4), (1, 4)],
        )

    def test_all_edges_tied(self):
        edges = [(0, 1, 2), (0, 2, 2), (0, 3, 2)]
        self.assertEqual(
            component_stats(4, edges, [1, 2, 2, 3]),
            [(4, 1), (1, 4), (1, 4), (1, 4)],
        )

    def test_duplicate_and_unsorted_queries_keep_original_order(self):
        edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5)]
        self.assertEqual(
            component_stats(5, edges, [3, 0, 5, 1, 2, 3]),
            [(2, 3), (5, 1), (1, 5), (4, 2), (3, 2), (2, 3)],
        )


class LargeScale(unittest.TestCase):
    def test_long_path_edges_in_reverse_order(self):
        n = 200_000
        edges = [(i, i + 1, i) for i in range(n - 2, -1, -1)]
        queries = [-1, 0, 1, 99_999, n - 2, 10**9]
        res = component_stats(n, edges, queries, include_summary=True)
        self.assertEqual(
            res["answers"],
            [
                (n, 1),
                (n - 1, 2),
                (n - 2, 3),
                (n - 100_000, 100_001),
                (1, n),
                (1, n),
            ],
        )
        s = res["operation_summary"]
        self.assertEqual(s["edges_processed"], n - 1)
        self.assertEqual(s["unions_performed"], n - 1)
        self.assertEqual(s["redundant_edges_skipped"], 0)

    def test_many_parallel_edges(self):
        edges = [(0, 1, 1)] * 10_000
        res = component_stats(2, edges, [0, 1], include_summary=True)
        self.assertEqual(res["answers"], [(2, 1), (1, 2)])
        s = res["operation_summary"]
        self.assertEqual(s["unions_performed"], 1)
        self.assertEqual(s["redundant_edges_skipped"], 9_999)
        self.assertEqual(s["edges_processed"], 10_000)

    def test_many_duplicate_queries(self):
        queries = [5] * 50_000
        res = component_stats(3, [(0, 1, 5)], queries)
        self.assertEqual(res, [(2, 2)] * 50_000)


class ContractChecks(unittest.TestCase):
    def test_summary_off_returns_plain_list(self):
        res = component_stats(2, [(0, 1, 1)], [1])
        self.assertIsInstance(res, list)

    def test_summary_on_answers_match_summary_off(self):
        edges = [(0, 1, 2), (1, 2, 2), (2, 3, 4)]
        queries = [2, 2, 1, 4]
        on = component_stats(4, edges, queries, include_summary=True)
        self.assertEqual(on["answers"], component_stats(4, edges, queries))
        s = on["operation_summary"]
        self.assertEqual(
            s["edges_processed"],
            s["unions_performed"] + s["redundant_edges_skipped"],
        )
        self.assertEqual(s["total_major_operations"], 3 + 4)

    def test_inputs_not_mutated(self):
        edges = [(2, 3, 5), (0, 1, 1)]
        queries = [5, 0]
        e_copy, q_copy = list(edges), list(queries)
        component_stats(4, edges, queries)
        self.assertEqual(edges, e_copy)
        self.assertEqual(queries, q_copy)

    def test_invalid_input_still_rejected(self):
        with self.assertRaises(ValueError):
            component_stats(-1, [], [1])
        with self.assertRaises(ValueError):
            component_stats(3, [(0, -1, 1)], [1])
        with self.assertRaises(ValueError):
            component_stats(3, [(0, 3, 1)], [1])
        with self.assertRaises(ValueError):
            component_stats(0, [(0, 0, 1)], [1])


class DeterministicCrossCheck(unittest.TestCase):
    def test_against_brute_force(self):
        state = 12345  # fixed-seed LCG, so the test is fully deterministic

        def nxt(mod):
            nonlocal state
            state = (state * 1103515245 + 12345) % (2**31)
            return state % mod

        for n in (1, 2, 3, 6, 9):
            for m in (0, 1, 5, 15):
                edges = [(nxt(n), nxt(n), nxt(7) - 3) for _ in range(m)]
                queries = [nxt(9) - 4 for _ in range(12)]
                self.assertEqual(
                    component_stats(n, edges, queries),
                    brute_force(n, edges, queries),
                    msg=f"n={n}, edges={edges}, queries={queries}",
                )


if __name__ == "__main__":
    unittest.main()