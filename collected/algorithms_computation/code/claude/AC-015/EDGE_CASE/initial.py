#!/usr/bin/env python3
"""
Deterministic Dinic's algorithm for Maximum Flow.

Input format (whitespace separated, read from stdin):
    n m s t
    u_1 v_1 c_1
    u_2 v_2 c_2
    ...
    u_m v_m c_m

    n : number of nodes, labeled 0..n-1
    m : number of directed edges
    s : source node
    t : sink node
    Each of the next m lines describes one directed edge u_i -> v_i
    with integer capacity c_i >= 0.

Output:
    First line: the maximum flow value.
    Next m lines: the flow on edge i (in original input order).

No network access, no randomness, no external services are used.
"""

import sys
from collections import deque


class Dinic:
    """Deterministic Dinic's blocking-flow max-flow algorithm."""

    def __init__(self, n):
        self.n = n
        # Adjacency list of arc indices, per node, in insertion order.
        self.graph = [[] for _ in range(n)]
        # Parallel arrays describing every arc (forward and reverse).
        self.arc_to = []       # destination node of arc i
        self.arc_cap = []      # remaining residual capacity of arc i
        # For each original input edge, the index of its forward arc.
        self.original_forward_arc = []
        # The original capacity of each input edge (to recover flow later).
        self.original_cap = []

    def add_edge(self, u, v, cap):
        """Add one directed capacitated edge u->v; returns nothing.
        Internally creates a forward arc (cap) and a reverse arc (0)."""
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
        """Build level graph via BFS. Returns level array, or None if t
        is unreachable from s (meaning current flow is already maximum)."""
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
        """Push up to `pushed` units of flow from u to t using only
        edges that strictly advance the level (u -> v with
        level[v] == level[u] + 1). `it` is the current-arc pointer
        array shared across the whole blocking-flow phase."""
        if u == t or pushed == 0:
            return pushed

        while it[u] < len(self.graph[u]):
            arc_id = self.graph[u][it[u]]
            v = self.arc_to[arc_id]
            cap = self.arc_cap[arc_id]

            if cap > 0 and level[v] == level[u] + 1:
                take = min(pushed, cap)
                got = self._dfs_blocking(v, t, take, level, it)
                if got > 0:
                    self.arc_cap[arc_id] -= got
                    self.arc_cap[arc_id ^ 1] += got  # arcs paired as 2k / 2k+1
                    return got
                else:
                    # Dead end from v at this phase: never look at it again.
                    level[v] = -1

            it[u] += 1

        return 0

    def max_flow(self, s, t):
        flow = 0
        while True:
            level = self._bfs_levels(s, t)
            if level is None:
                break
            it = [0] * self.n
            # Keep finding augmenting paths within this level graph
            # until it is exhausted (this constitutes one blocking flow).
            while True:
                pushed = self._dfs_blocking(s, t, float('inf'), level, it)
                if pushed == 0:
                    break
                flow += pushed
        return flow

    def edge_flow(self, i):
        """Flow actually sent along original input edge i, in original order."""
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
    flows = [dinic.edge_flow(i) for i in range(m)]  # original edge order preserved

    out_lines = [str(max_flow_value)]
    out_lines.extend(str(f) for f in flows)
    return "\n".join(out_lines)


def main():
    input_text = sys.stdin.read()
    print(solve(input_text))


if __name__ == "__main__":
    main()