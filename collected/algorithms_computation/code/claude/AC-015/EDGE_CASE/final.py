#!/usr/bin/env python3
"""
Deterministic Dinic's algorithm for Maximum Flow, with explicit handling
of boundary/edge-limit cases.

Input format (whitespace separated, read from stdin):
    n m s t
    u_1 v_1 c_1
    ...
    u_m v_m c_m

Output:
    First line: the maximum flow value.
    Next m lines: the flow on edge i, in original input order.

No network access, no randomness, no external services, no floating point
used for capacities/flow (an exact integer sentinel replaces float('inf')).
"""

import sys
import unittest
from collections import deque


class Dinic:
    """Deterministic Dinic's blocking-flow max-flow algorithm."""

    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]   # adjacency: arc indices, insertion order
        self.arc_to = []
        self.arc_cap = []
        self.original_forward_arc = []
        self.original_cap = []

    def add_edge(self, u, v, cap):
        """Add one directed capacitated edge u->v (self-loops and parallel
        edges are both allowed and tracked independently)."""
        fwd_index = len(self.arc_to)
        self.arc_to.append(v)
        self.arc_cap.append(cap)
        self.graph[u].append(fwd_index)

        rev_index = len(self.arc_to)
        self.arc_to.append(u)
        self.arc_cap.append(0)
        self.graph[v].append(rev_index)

        self.original_forward_arc.append(fwd_index)
        self.original_cap.append(cap)

    def _bfs_levels(self, s, t):
        level = [-1] * self.n
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for arc_id in self.graph[u]:
                if self.arc_cap[arc_id] > 0:
                    v = self.arc_to[arc_id]
                    if level[v] == -1:
                        level[v] = level[u] + 1
                        q.append(v)
        return level if level[t] != -1 else None

    def _dfs_blocking(self, u, t, pushed, level, it):
        if u == t or pushed == 0:
            return pushed

        while it[u] < len(self.graph[u]):
            arc_id = self.graph[u][it[u]]
            v = self.arc_to[arc_id]
            cap = self.arc_cap[arc_id]

            # Self-loops (v == u) can never satisfy level[v] == level[u] + 1,
            # so they are naturally and safely skipped here.
            if cap > 0 and level[v] == level[u] + 1:
                take = min(pushed, cap)
                got = self._dfs_blocking(v, t, take, level, it)
                if got > 0:
                    self.arc_cap[arc_id] -= got
                    self.arc_cap[arc_id ^ 1] += got
                    return got
                else:
                    level[v] = -1
            it[u] += 1

        return 0

    def max_flow(self, s, t):
        # Boundary case: s == t. No meaningful flow is required (s and t
        # are excluded from conservation constraints when distinct; when
        # they coincide there is nothing to conserve), so the answer is
        # exactly 0 and every edge carries 0 flow.
        if s == t:
            return 0

        # Exact integer sentinel for "unlimited", sized to safely dominate
        # any real bottleneck (sum of all capacities + 1), avoiding any
        # float/int mixing even for very large capacity values.
        total_cap = sum(self.original_cap) if self.original_cap else 0
        INF = total_cap + 1

        flow = 0
        while True:
            level = self._bfs_levels(s, t)
            if level is None:
                break
            it = [0] * self.n
            while True:
                pushed = self._dfs_blocking(s, t, INF, level, it)
                if pushed == 0:
                    break
                flow += pushed
        return flow

    def edge_flow(self, i):
        arc_id = self.original_forward_arc[i]
        return self.original_cap[i] - self.arc_cap[arc_id]


def solve(input_text):
    data = input_text.split()
    idx = 0

    def read_int():
        nonlocal idx
        val = int(data[idx])
        idx += 1
        return val

    n = read_int()
    m = read_int()
    s = read_int()
    t = read_int()

    dinic = Dinic(n)
    for _ in range(m):
        u = read_int()
        v = read_int()
        c = read_int()
        dinic.add_edge(u, v, c)

    max_flow_value = dinic.max_flow(s, t)
    flows = [dinic.edge_flow(i) for i in range(m)]  # original order preserved

    out_lines = [str(max_flow_value)]
    out_lines.extend(str(f) for f in flows)
    return "\n".join(out_lines)


def main():
    input_text = sys.stdin.read()
    print(solve(input_text))


# --------------------------------------------------------------------------
# Tests: standard-library unittest, fully deterministic, no randomness.
# --------------------------------------------------------------------------

def _verify_feasible(n, edges, s, t, flows, max_flow_value):
    """Independent checker: capacity, conservation, and value consistency."""
    assert len(edges) == len(flows)
    net = [0] * n
    for (u, v, c), f in zip(edges, flows):
        assert 0 <= f <= c, f"capacity violated: f={f} c={c}"
        if u != v:  # self-loops don't affect net balance
            net[u] -= f
            net[v] += f
    if s != t:
        for node in range(n):
            if node not in (s, t):
                assert net[node] == 0, f"conservation violated at node {node}"
        assert net[s] == -max_flow_value
        assert net[t] == max_flow_value
    else:
        assert max_flow_value == 0


class TestMaxFlowPlanner(unittest.TestCase):

    def _run(self, n, edges, s, t):
        d = Dinic(n)
        for u, v, c in edges:
            d.add_edge(u, v, c)
        value = d.max_flow(s, t)
        flows = [d.edge_flow(i) for i in range(len(edges))]
        return value, flows

    def test_basic_known_flow(self):
        edges = [(0, 1, 3), (0, 2, 2), (1, 2, 1), (1, 3, 2), (2, 3, 3)]
        value, flows = self._run(4, edges, 0, 3)
        self.assertEqual(value, 4)
        _verify_feasible(4, edges, 0, 3, flows, value)

    def test_s_equals_t_multi_node(self):
        edges = [(0, 1, 5), (1, 2, 5)]
        value, flows = self._run(3, edges, 1, 1)
        self.assertEqual(value, 0)
        self.assertEqual(flows, [0, 0])
        _verify_feasible(3, edges, 1, 1, flows, value)

    def test_single_node_reflexive(self):
        # n == 1 boundary, no edges at all, s == t == 0.
        value, flows = self._run(1, [], 0, 0)
        self.assertEqual(value, 0)
        self.assertEqual(flows, [])

    def test_no_edges_distinct_st(self):
        value, flows = self._run(2, [], 0, 1)
        self.assertEqual(value, 0)
        self.assertEqual(flows, [])

    def test_disconnected_graph(self):
        edges = [(0, 1, 10), (2, 3, 10)]  # s=0,t=3 not connected
        value, flows = self._run(4, edges, 0, 3)
        self.assertEqual(value, 0)
        self.assertEqual(flows, [0, 0])
        _verify_feasible(4, edges, 0, 3, flows, value)

    def test_zero_capacity_edges(self):
        edges = [(0, 1, 0), (0, 2, 5), (2, 1, 5), (1, 3, 0), (2, 3, 5)]
        value, flows = self._run(4, edges, 0, 3)
        self.assertEqual(flows[0], 0)  # forced zero
        self.assertEqual(flows[3], 0)  # forced zero
        _verify_feasible(4, edges, 0, 3, flows, value)
        self.assertEqual(value, 5)

    def test_self_loop_does_not_break_or_help(self):
        edges = [(0, 0, 100), (0, 1, 4), (1, 1, 50), (1, 2, 4)]
        value, flows = self._run(3, edges, 0, 2)
        self.assertEqual(value, 4)
        self.assertEqual(flows[0], 0)  # self loop at s carries no net flow
        self.assertEqual(flows[2], 0)  # self loop at intermediate node
        _verify_feasible(3, edges, 0, 2, flows, value)

    def test_parallel_and_antiparallel_edges(self):
        edges = [
            (0, 1, 3),
            (0, 1, 4),   # parallel edge, same direction
            (1, 0, 2),   # anti-parallel edge
            (1, 2, 10),
        ]
        value, flows = self._run(3, edges, 0, 2)
        self.assertEqual(value, 7)  # bounded by 3+4 into node 1
        self.assertEqual(len(flows), 4)
        _verify_feasible(3, edges, 0, 2, flows, value)

    def test_large_capacity_values(self):
        big = 2**31 - 1
        bigger = 10**18
        edges = [(0, 1, big), (1, 2, bigger), (0, 2, 1)]
        value, flows = self._run(3, edges, 0, 2)
        self.assertEqual(value, big + 1)
        _verify_feasible(3, edges, 0, 2, flows, value)

    def test_moderate_scale_grid_deterministic(self):
        # Deterministic (non-random) layered graph to sanity-check scaling.
        layers, width = 6, 5
        n = layers * width + 2
        s, t = n - 2, n - 1
        edges = []
        for L in range(layers):
            for w in range(width):
                node = L * width + w
                if L == 0:
                    edges.append((s, node, w + 1))
                if L == layers - 1:
                    edges.append((node, t, w + 1))
                if L + 1 < layers:
                    nxt = (L + 1) * width + w
                    edges.append((node, nxt, (w + 1) * 2))
        value, flows = self._run(n, edges, s, t)
        _verify_feasible(n, edges, s, t, flows, value)
        self.assertGreater(value, 0)

    def test_output_preserves_original_edge_order(self):
        # Edges listed in a deliberately "scrambled" order relative to a
        # natural traversal; output must still match input order exactly.
        edges = [(2, 3, 5), (0, 2, 5), (0, 1, 5), (1, 3, 5)]
        value, flows = self._run(4, edges, 0, 3)
        self.assertEqual(len(flows), len(edges))
        _verify_feasible(4, edges, 0, 3, flows, value)
        # Edge index 0 is (2,3,5) — check its reported flow individually
        # to confirm the mapping wasn't reordered.
        self.assertTrue(0 <= flows[0] <= 5)

    def test_solve_stdin_format_roundtrip(self):
        text = "4 5 0 3\n0 1 3\n0 2 2\n1 2 1\n1 3 2\n2 3 3\n"
        result = solve(text)
        lines = result.strip().split("\n")
        self.assertEqual(int(lines[0]), 4)
        self.assertEqual(len(lines), 1 + 5)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.argv = sys.argv[:1]
        unittest.main()
    else:
        main()