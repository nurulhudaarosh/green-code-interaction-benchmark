#!/usr/bin/env python3
"""
Deterministic Dinic's max-flow algorithm.

Input format (stdin):
    n m s t
    u1 v1 cap1
    u2 v2 cap2
    ...
    um vm capm

Nodes are 0-indexed integers in [0, n).
Output (stdout):
    max_flow_value
    f1
    f2
    ...
    fm      (flow on each edge, in original input order)
"""

import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        # graph[u] = list of arc indices incident from u
        self.graph = [[] for _ in range(n)]
        # arcs stored as [to, capacity]; arcs come in forward/backward pairs
        # arc index k (even) is forward, k^1 is its paired reverse arc
        self.to = []
        self.cap = []

    def add_edge(self, u, v, capacity):
        """Adds a directed edge u->v with given capacity.
        Returns the arc index of the forward arc (needed to read back flow)."""
        fwd_idx = len(self.to)
        self.to.append(v)
        self.cap.append(capacity)
        self.graph[u].append(fwd_idx)

        rev_idx = len(self.to)
        self.to.append(u)
        self.cap.append(0)
        self.graph[v].append(rev_idx)

        return fwd_idx

    def bfs_levels(self, s, t):
        level = [-1] * self.n
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for arc_idx in self.graph[u]:
                if self.cap[arc_idx] > 0 and level[self.to[arc_idx]] < 0:
                    level[self.to[arc_idx]] = level[u] + 1
                    q.append(self.to[arc_idx])
        return level if level[t] >= 0 else None

    def dfs_blocking(self, u, t, level, it, pushed):
        if u == t:
            return pushed
        while it[u] < len(self.graph[u]):
            arc_idx = self.graph[u][it[u]]
            v = self.to[arc_idx]
            if self.cap[arc_idx] > 0 and level[v] == level[u] + 1:
                d = self.dfs_blocking(v, t, level, it, min(pushed, self.cap[arc_idx]))
                if d > 0:
                    self.cap[arc_idx] -= d
                    self.cap[arc_idx ^ 1] += d
                    return d
            it[u] += 1
        return 0

    def max_flow(self, s, t):
        flow = 0
        while True:
            level = self.bfs_levels(s, t)
            if level is None:
                break
            it = [0] * self.n
            while True:
                pushed = self.dfs_blocking(s, t, level, it, float('inf'))
                if pushed == 0:
                    break
                flow += pushed
        return flow


def solve(input_text):
    tokens = input_text.split()
    idx = 0

    def next_int():
        nonlocal idx
        val = int(tokens[idx])
        idx += 1
        return val

    n = next_int()
    m = next_int()
    s = next_int()
    t = next_int()

    din = Dinic(n)
    fwd_arc_of_edge = []       # original-edge-index -> forward arc index
    original_capacity = []    # original-edge-index -> capacity

    for _ in range(m):
        u = next_int()
        v = next_int()
        c = next_int()
        arc_idx = din.add_edge(u, v, c)
        fwd_arc_of_edge.append(arc_idx)
        original_capacity.append(c)

    max_flow_value = din.max_flow(s, t)

    # flow on edge i = original capacity - remaining residual capacity of its forward arc
    edge_flows = [
        original_capacity[i] - din.cap[fwd_arc_of_edge[i]]
        for i in range(m)
    ]

    out_lines = [str(max_flow_value)]
    out_lines.extend(str(f) for f in edge_flows)
    return "\n".join(out_lines)


def main():
    input_text = sys.stdin.read()
    if not input_text.strip():
        return
    print(solve(input_text))


if __name__ == "__main__":
    main()