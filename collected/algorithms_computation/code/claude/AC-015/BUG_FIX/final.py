#!/usr/bin/env python3
"""
Maximum Flow Planner — Dinic's blocking-flow algorithm.

Problem:
    Given a directed capacitated graph (n nodes, m edges, source s, sink t),
    compute the maximum s-t flow value and the flow on every original edge.

Constraints enforced:
    - 0 <= f[i] <= cap[i] for every edge i
    - Flow conservation at every node except s and t
    - Output must be EXACTLY the required result with deterministic tie
      handling: among multiple valid max-flow solutions, ties are always
      broken by preferring the admissible edge with the smallest ORIGINAL
      INPUT INDEX. This is enforced structurally (adjacency lists are sorted
      by original edge index before running the algorithm), not left to
      incidental call order, so output is a pure function of the declared
      input regardless of internal construction order.
    - Edge flows are reported in original input order.
    - Standard library only. No network, no randomness, no human interaction.

Input format (stdin):
    n m s t
    u1 v1 cap1
    ...
    um vm capm

Output (stdout):
    max_flow_value
    f1
    ...
    fm
"""

import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]   # graph[u] = list of arc indices
        self.to = []
        self.cap = []
        self.orig_edge_id = []   # orig_edge_id[arc_idx] = original edge index, -1 for reverse arcs
        self._finalized = False

    def add_edge(self, u, v, capacity, orig_index):
        """Adds directed edge u->v with given capacity, tagged with its
        original input index (used only for deterministic tie-breaking)."""
        fwd_idx = len(self.to)
        self.to.append(v)
        self.cap.append(capacity)
        self.orig_edge_id.append(orig_index)
        self.graph[u].append(fwd_idx)

        rev_idx = len(self.to)
        self.to.append(u)
        self.cap.append(0)
        self.orig_edge_id.append(-1)   # reverse arcs never win a tie-break directly
        self.graph[v].append(rev_idx)

        return fwd_idx

    def finalize(self):
        """Must be called once, after all add_edge calls, before max_flow.
        Pins the deterministic tie-break rule: at every node, arcs are
        explored in ascending original-edge-index order (a reverse arc is
        ordered by its paired forward edge's index)."""
        for u in range(self.n):
            self.graph[u].sort(
                key=lambda arc_idx: (
                    self.orig_edge_id[arc_idx]
                    if self.orig_edge_id[arc_idx] >= 0
                    else self.orig_edge_id[arc_idx ^ 1]
                )
            )
        self._finalized = True

    def bfs_levels(self, s, t):
        level = [-1] * self.n
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for arc_idx in self.graph[u]:      # canonical (sorted) order
                if self.cap[arc_idx] > 0 and level[self.to[arc_idx]] < 0:
                    level[self.to[arc_idx]] = level[u] + 1
                    q.append(self.to[arc_idx])
        return level if level[t] >= 0 else None

    def dfs_blocking(self, u, t, level, it, pushed):
        if u == t:
            return pushed
        while it[u] < len(self.graph[u]):
            arc_idx = self.graph[u][it[u]]      # canonical order -> deterministic ties
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
        assert self._finalized, "finalize() must be called before max_flow()"
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
    fwd_arc_of_edge = []
    original_capacity = []

    for i in range(m):
        u = next_int()
        v = next_int()
        c = next_int()
        arc_idx = din.add_edge(u, v, c, orig_index=i)
        fwd_arc_of_edge.append(arc_idx)
        original_capacity.append(c)

    din.finalize()
    max_flow_value = din.max_flow(s, t)

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