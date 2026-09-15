#!/usr/bin/env python3
"""
Deterministic maximum s-t flow via Dinic's blocking-flow algorithm.

- Standard library only (uses collections.deque for BFS).
- No randomness, no network/API/human-interaction dependence.
- Supports parallel edges and self-loops.
- Returns per-edge flow values in the SAME ORDER the edges were supplied.
- All flow arithmetic is exact integer arithmetic (no floats), guaranteeing
  deterministic, reproducible results across runs/platforms.

Input format (stdin), if run as a script:
    n m s t
    u1 v1 cap1
    u2 v2 cap2
    ...
    um vm capm

Output (stdout):
    <max_flow_value>
    <flow on edge 1>
    <flow on edge 2>
    ...
    <flow on edge m>
"""

from collections import deque
from typing import List, Tuple

INF = 1 << 62  # integer sentinel for "unbounded" push amount


class Dinic:
    """
    Deterministic Dinic's algorithm.

    Internal representation: flat arrays `to[]` and `cap[]` hold every arc
    (forward and reverse). For an edge added at call j, its forward arc is
    stored at index 2*j and its reverse (residual) arc at index 2*j + 1.
    graph[u] lists arc indices leaving u, always appended in the order the
    edges were added, so BFS/DFS traversal order is fully determined by
    input order (no sets, no hashing of vertices used for iteration).
    """

    def __init__(self, n: int):
        self.n = n
        self.graph: List[List[int]] = [[] for _ in range(n)]
        self.to: List[int] = []
        self.cap: List[int] = []

    def add_edge(self, u: int, v: int, capacity: int) -> int:
        """Add a directed edge u->v with given capacity. Returns the
        forward-arc index (used later to recover flow on this edge)."""
        if capacity < 0:
            raise ValueError("edge capacities must be non-negative")
        if not isinstance(capacity, int):
            raise TypeError("edge capacities must be integers for exact, "
                             "deterministic flow computation")
        fwd_index = len(self.to)
        self.graph[u].append(fwd_index)
        self.to.append(v)
        self.cap.append(capacity)

        rev_index = len(self.to)
        self.graph[v].append(rev_index)
        self.to.append(u)
        self.cap.append(0)  # reverse arc starts with zero residual capacity

        return fwd_index

    def _bfs_levels(self, s: int, t: int) -> List[int]:
        """Build level graph from s. level[v] = -1 if unreachable."""
        level = [-1] * self.n
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            if u == t:
                continue
            for arc in self.graph[u]:
                v = self.to[arc]
                if self.cap[arc] > 0 and level[v] == -1:
                    level[v] = level[u] + 1
                    q.append(v)
        return level

    def _dfs_blocking(self, u: int, t: int, pushed: int,
                       level: List[int], it: List[int]) -> int:
        """Push up to `pushed` units of flow along level-respecting paths
        from u to t; iterative-friendly via current-arc pointers `it`.
        `pushed` and all returned/propagated values remain plain ints."""
        if u == t or pushed == 0:
            return pushed
        while it[u] < len(self.graph[u]):
            arc = self.graph[u][it[u]]
            v = self.to[arc]
            if self.cap[arc] > 0 and level[v] == level[u] + 1:
                delta = self._dfs_blocking(
                    v, t, min(pushed, self.cap[arc]), level, it
                )
                if delta > 0:
                    self.cap[arc] -= delta
                    self.cap[arc ^ 1] += delta
                    return delta
            it[u] += 1
        return 0

    def max_flow(self, s: int, t: int) -> int:
        """Compute and return the maximum flow value from s to t (int).
        After calling this, per-edge flow can be recovered via
        `flow_on_edge(forward_index, original_capacity)`."""
        if s == t:
            return 0

        total_flow = 0
        while True:
            level = self._bfs_levels(s, t)
            if level[t] == -1:
                break  # t unreachable: current flow is maximum

            it = [0] * self.n
            while True:
                pushed = self._dfs_blocking(s, t, INF, level, it)
                if pushed == 0:
                    break
                total_flow += pushed

        return total_flow

    def flow_on_edge(self, fwd_index: int, original_capacity: int) -> int:
        """Recover the flow actually sent on the edge whose forward arc
        is stored at fwd_index (as returned by add_edge)."""
        return original_capacity - self.cap[fwd_index]


def max_flow_with_edge_flows(
    n: int,
    edges: List[Tuple[int, int, int]],
    s: int,
    t: int,
) -> Tuple[int, List[int]]:
    """
    Compute max flow and per-edge flow values, preserving input edge order.

    Parameters
    ----------
    n     : number of vertices, labeled 0..n-1
    edges : list of (u, v, capacity) tuples, in the order they should be
            reported back
    s, t  : source and sink vertex indices

    Returns
    -------
    (max_flow_value, flows) where flows[i] is the flow assigned to
    edges[i], in the same order as the input list. Both the total and
    each entry in flows are exact Python ints.
    """
    din = Dinic(n)
    fwd_indices = []
    for (u, v, c) in edges:
        fwd_indices.append(din.add_edge(u, v, c))

    total = din.max_flow(s, t)

    flows = [
        din.flow_on_edge(fwd_indices[i], edges[i][2])
        for i in range(len(edges))
    ]
    return total, flows


def _read_input() -> Tuple[int, List[Tuple[int, int, int]], int, int]:
    import sys
    data = sys.stdin.read().split()
    idx = 0

    def next_int():
        nonlocal idx
        val = int(data[idx])
        idx += 1
        return val

    n = next_int()
    m = next_int()
    s = next_int()
    t = next_int()
    edges = []
    for _ in range(m):
        u = next_int()
        v = next_int()
        c = next_int()
        edges.append((u, v, c))
    return n, edges, s, t


def _self_test():
    """Small deterministic sanity check (classic textbook example)."""
    edges = [
        (0, 1, 16),
        (0, 2, 13),
        (1, 2, 10),
        (2, 1, 4),
        (1, 3, 12),
        (3, 2, 9),
        (2, 4, 14),
        (4, 3, 7),
        (3, 5, 20),
        (4, 5, 4),
    ]
    total, flows = max_flow_with_edge_flows(6, edges, 0, 5)
    assert total == 23, f"expected max flow 23, got {total}"
    assert isinstance(total, int), "max flow value must be an exact int"
    for (u, v, cap), f in zip(edges, flows):
        assert isinstance(f, int), f"flow on edge ({u},{v},{cap}) must be an exact int, got {type(f)}"
        assert 0 <= f <= cap, f"edge ({u},{v},{cap}) got invalid flow {f}"
    print("Self-test passed. Max flow =", total)
    print("Per-edge flows (original order):", flows)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        _self_test()
    else:
        n, edges, s, t = _read_input()
        total, flows = max_flow_with_edge_flows(n, edges, s, t)
        print(total)
        for f in flows:
            print(f)