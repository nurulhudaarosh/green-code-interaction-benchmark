import unittest
from typing import List, Tuple, Sequence


def components_by_threshold(
    n: int,
    edges: Sequence[Tuple[int, int, float]],
    queries: Sequence[float],
) -> List[Tuple[int, int]]:
    parent = list(range(n))
    size = [1] * n
    components = n
    largest = 1 if n > 0 else 0

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    sorted_edges = sorted(edges, key=lambda e: e[2])
    order = sorted(range(len(queries)), key=lambda i: queries[i])

    answers: List[Tuple[int, int]] = [(0, 0)] * len(queries)
    ei = 0
    m = len(sorted_edges)

    for qi in order:
        q = queries[qi]
        while ei < m and sorted_edges[ei][2] <= q:
            u, v, _ = sorted_edges[ei]
            ei += 1
            ru, rv = find(u), find(v)
            if ru != rv:
                if size[ru] < size[rv]:
                    ru, rv = rv, ru
                parent[rv] = ru
                size[ru] += size[rv]
                components -= 1
                if size[ru] > largest:
                    largest = size[ru]
        answers[qi] = (components, largest)

    return answers


def brute_force(n, edges, queries):
    """Reference: recompute from scratch per query (small inputs only)."""
    res = []
    for q in queries:
        adj = [[] for _ in range(n)]
        for u, v, w in edges:
            if w <= q:
                adj[u].append(v)
                adj[v].append(u)
        seen = [False] * n
        comps, best = 0, 0
        for s in range(n):
            if seen[s]:
                continue
            comps += 1
            stack, cnt = [s], 0
            seen[s] = True
            while stack:
                x = stack.pop()
                cnt += 1
                for y in adj[x]:
                    if not seen[y]:
                        seen[y] = True
                        stack.append(y)
            best = max(best, cnt)
        res.append((comps, best))
    return res


class TestThresholdConnectivity(unittest.TestCase):
    def test_original_example(self):
        edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5), (4, 5, 7)]
        queries = [0, 1, 2, 3, 5, 7, 4]
        self.assertEqual(
            components_by_threshold(6, edges, queries),
            [(6, 1), (5, 2), (4, 2), (3, 3), (2, 5), (1, 6), (3, 3)],
        )

    def test_n_zero(self):
        self.assertEqual(components_by_threshold(0, [], [5, -5]), [(0, 0), (0, 0)])

    def test_empty_queries(self):
        self.assertEqual(components_by_threshold(3, [(0, 1, 1)], []), [])

    def test_single_vertex_self_loop(self):
        self.assertEqual(
            components_by_threshold(1, [(0, 0, 1)], [0, 1, 2]),
            [(1, 1)] * 3,
        )

    def test_no_edges(self):
        self.assertEqual(components_by_threshold(3, [], [0, 100]), [(3, 1)] * 2)

    def test_equality_included_at_min_and_max(self):
        edges = [(0, 1, 5), (1, 2, 9)]
        self.assertEqual(
            components_by_threshold(3, edges, [4, 5, 8, 9, 10]),
            [(3, 1), (2, 2), (2, 2), (1, 3), (1, 3)],
        )

    def test_all_equal_weights_tie(self):
        edges = [(0, 1, 5), (1, 2, 5), (2, 3, 5)]
        self.assertEqual(
            components_by_threshold(4, edges, [4, 5]), [(4, 1), (1, 4)]
        )
        self.assertEqual(
            components_by_threshold(4, edges[::-1], [4, 5]), [(4, 1), (1, 4)]
        )

    def test_negative_zero_and_infinite_weights(self):
        inf = float("inf")
        edges = [(0, 1, -inf), (1, 2, inf)]
        self.assertEqual(
            components_by_threshold(3, edges, [-inf, 0, inf]),
            [(2, 2), (2, 2), (1, 3)],
        )

    def test_huge_integers(self):
        big = 10**18
        edges = [(0, 1, -big), (1, 2, big)]
        self.assertEqual(
            components_by_threshold(3, edges, [-big - 1, -big, big - 1, big]),
            [(3, 1), (2, 2), (2, 2), (1, 3)],
        )

    def test_float_rounding(self):
        edges = [(0, 1, 0.3)]
        self.assertEqual(components_by_threshold(2, edges, [0.1 + 0.2]), [(1, 2)])
        self.assertEqual(components_by_threshold(2, edges, [0.3]), [(1, 2)])

    def test_self_loops_and_parallel_edges(self):
        edges = [(0, 0, 1), (0, 1, 2), (0, 1, 2), (1, 1, 0)]
        self.assertEqual(
            components_by_threshold(2, edges, [0, 1, 2]),
            [(2, 1), (2, 1), (1, 2)],
        )

    def test_duplicate_and_unsorted_queries_keep_order(self):
        edges = [(0, 1, 1), (1, 2, 3)]
        self.assertEqual(
            components_by_threshold(3, edges, [3, 0, 3, 1, 0]),
            [(1, 3), (3, 1), (1, 3), (2, 2), (3, 1)],
        )

    def test_large_n_no_edges(self):
        n = 10**6
        self.assertEqual(components_by_threshold(n, [], [0]), [(n, 1)])

    def test_long_chain_no_recursion_issue(self):
        n = 100_000
        edges = [(i, i + 1, i) for i in range(n - 1)]  # worst-case ordering
        res = components_by_threshold(n, edges, [-1, n // 2, n])
        self.assertEqual(res[0], (n, 1))
        self.assertEqual(res[1], (n - (n // 2 + 1), n // 2 + 2))
        self.assertEqual(res[2], (1, n))

    def test_against_brute_force_deterministic(self):
        state = 12345

        def rnd(k):  # fixed LCG, fully deterministic
            nonlocal state
            state = (state * 1103515245 + 12345) % (2**31)
            return state % k

        for _ in range(200):
            n = rnd(8)
            edges = (
                [(rnd(n), rnd(n), rnd(6) - 1) for _ in range(rnd(12))] if n else []
            )
            queries = [rnd(8) - 2 for _ in range(rnd(8))]
            self.assertEqual(
                components_by_threshold(n, edges, queries),
                brute_force(n, edges, queries),
            )


if __name__ == "__main__":
    unittest.main()