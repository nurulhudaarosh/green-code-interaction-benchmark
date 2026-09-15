#!/usr/bin/env python3
"""
Deterministic Maximum Flow via Dinic's Blocking-Flow Algorithm.

Problem
-------
Given a directed capacitated graph, a source s and a sink t, compute:
  1. The maximum s-t flow value.
  2. The flow assigned to every ORIGINAL input edge, in the same order
     the edges were given.

Constraints enforced by construction
-------------------------------------
  - 0 <= f(e) <= cap(e) for every original edge e.
  - Flow conservation at every vertex other than s and t.
  - Output edge order == input edge order (parallel edges and self
    loops are each tracked independently).

Optional feature: operation_summary
------------------------------------
When explicitly requested (via solve(..., include_summary=True) or the
CLI flag --summary), an additional deterministic summary of the major
computational decisions made by the algorithm is produced:
  - bfs_phases              : number of level-graph (BFS) rebuilds
  - augmenting_paths_found  : number of blocking-flow paths pushed
  - edges_saturated         : number of residual arcs driven to zero
  - dead_ends_pruned        : number of vertices pruned during DFS
  - total_major_operations  : sum of the above four counts

This feature is OFF by default. When disabled or not requested, all
original outputs (max flow value, per-edge flow in input order) are
produced exactly as before, with no extra fields or behavioral change.

Algorithm
---------
Dinic's algorithm:
  1. Build a residual graph where every original edge (u, v, cap)
     contributes a forward arc (u->v, capacity cap) and a paired
     backward arc (v->u, capacity 0), stored at consecutive indices
     2*i and 2*i+1 in a flat edge list. The forward arc's index is
     remembered per original edge so we can read back its flow later.
  2. Repeat:
       a. BFS from s using only arcs with positive residual capacity
          to build a level graph (shortest-path distances from s).
          If t is unreachable, stop: current flow is maximum.
       b. DFS on the level graph with current-arc pointers to send
          a blocking flow (all flow along shortest augmenting paths
          for this phase), updating forward/backward residual
          capacities as we go.
  3. Flow on original edge i = original_capacity_i - residual_capacity
     of its forward arc (index 2*i) at termination.

This implementation is fully deterministic: no randomness, no
dependence on dict/set iteration order, no I/O beyond stdin/stdout,
and no network or external-service access. Standard library only.
"""

from collections import deque
import sys


class Dinic:
    """Deterministic Dinic's maximum flow algorithm, with optional
    instrumentation of major computational decisions."""

    def __init__(self, n_vertices):
        self.n = n_vertices
        # adjacency: graph[u] = list of arc indices leaving u (insertion order preserved)
        self.graph = [[] for _ in range(n_vertices)]
        # flat arc list: edges[i] = [to_vertex, residual_capacity]
        self.edges = []

        # --- operation counters (always tracked; only reported if requested) ---
        self.bfs_phases = 0
        self.augmenting_paths_found = 0
        self.edges_saturated = 0
        self.dead_ends_pruned = 0

    def add_edge(self, u, v, capacity):
        """
        Add a directed edge u -> v with the given capacity.
        Returns the index of the forward arc (needed to recover flow later).
        """
        if capacity < 0:
            raise ValueError("Capacities must be non-negative.")
        forward_idx = len(self.edges)
        self.edges.append([v, capacity])       # forward arc: u -> v
        self.edges.append([u, 0])              # backward arc: v -> u (starts at 0)
        self.graph[u].append(forward_idx)
        self.graph[v].append(forward_idx + 1)
        return forward_idx

    def _bfs_levels(self, s, t):
        level = [-1] * self.n
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for arc_id in self.graph[u]:
                v, cap = self.edges[arc_id]
                if cap > 0 and level[v] < 0:
                    level[v] = level[u] + 1
                    q.append(v)
        self.level = level
        found = level[t] >= 0
        if found:
            self.bfs_phases += 1  # major decision: a new level graph was accepted
        return found

    def _dfs_blocking(self, u, t, pushed):
        """Iterative DFS with current-arc pointers to avoid recursion-depth issues."""
        path_arcs = []          # arcs currently on the DFS path
        path_vertices = [u]     # vertices currently on the DFS path
        while True:
            cur = path_vertices[-1]
            if cur == t:
                # Found an augmenting path: bottleneck = min residual cap along it
                bottleneck = min(self.edges[a][1] for a in path_arcs) if path_arcs else pushed
                bottleneck = min(bottleneck, pushed)
                for a in path_arcs:
                    self.edges[a][1] -= bottleneck
                    self.edges[a ^ 1][1] += bottleneck
                    if self.edges[a][1] == 0:
                        self.edges_saturated += 1  # major decision: arc fully committed
                self.augmenting_paths_found += 1   # major decision: path chosen & pushed
                return bottleneck

            advanced = False
            while self.it[cur] < len(self.graph[cur]):
                arc_id = self.graph[cur][self.it[cur]]
                v, cap = self.edges[arc_id]
                if cap > 0 and self.level[v] == self.level[cur] + 1:
                    path_arcs.append(arc_id)
                    path_vertices.append(v)
                    advanced = True
                    break
                else:
                    self.it[cur] += 1
            if advanced:
                continue

            # Dead end: cur cannot reach t further in this level graph, kill it.
            self.level[cur] = -1
            self.dead_ends_pruned += 1  # major decision: vertex pruned from level graph
            if len(path_vertices) == 1:
                return 0  # back at the DFS root with nowhere to go
            path_vertices.pop()
            path_arcs.pop()
            parent = path_vertices[-1]
            # advance parent's pointer past the arc that just died
            self.it[parent] += 1

    def max_flow(self, s, t):
        if s == t:
            return 0
        total_flow = 0
        while self._bfs_levels(s, t):
            self.it = [0] * self.n
            while True:
                pushed = self._dfs_blocking(s, t, float("inf"))
                if pushed == 0:
                    break
                total_flow += pushed
        return total_flow

    def edge_flow(self, forward_idx, original_capacity):
        """Flow actually sent on the original edge with this forward arc index."""
        residual = self.edges[forward_idx][1]
        return original_capacity - residual

    def operation_summary(self):
        """Deterministic summary of major computational decisions made."""
        total = (
            self.bfs_phases
            + self.augmenting_paths_found
            + self.edges_saturated
            + self.dead_ends_pruned
        )
        return {
            "bfs_phases": self.bfs_phases,
            "augmenting_paths_found": self.augmenting_paths_found,
            "edges_saturated": self.edges_saturated,
            "dead_ends_pruned": self.dead_ends_pruned,
            "total_major_operations": total,
        }


def solve(n, edges_in, s, t, include_summary=False):
    """
    n                : number of vertices, labeled 0..n-1
    edges_in         : list of (u, v, capacity) in original input order
    s, t             : source and sink vertex labels
    include_summary  : if True, also return an operation_summary dict.
                        Default False preserves the original return
                        contract exactly.

    Returns:
      (max_flow_value, flows)                         if include_summary is False
      (max_flow_value, flows, operation_summary_dict)  if include_summary is True
    """
    dinic = Dinic(n)
    forward_indices = []
    for (u, v, cap) in edges_in:
        fidx = dinic.add_edge(u, v, cap)
        forward_indices.append(fidx)

    max_flow_value = dinic.max_flow(s, t)

    flows = [
        dinic.edge_flow(fidx, cap)
        for fidx, (_, _, cap) in zip(forward_indices, edges_in)
    ]

    if include_summary:
        return max_flow_value, flows, dinic.operation_summary()
    return max_flow_value, flows


def main():
    """
    Expected stdin format (UNCHANGED from the original spec):
        n m s t
        u1 v1 cap1
        u2 v2 cap2
        ...
        um vm capm

    Vertices are 0-indexed integers in [0, n).

    Output (unchanged when the feature is not requested):
        First line: maximum flow value.
        Next m lines: flow on the i-th input edge (same order as input).

    Optional feature (opt-in only, via CLI flag):
        Pass --summary as a command-line argument to additionally print
        an "OPERATION_SUMMARY" section after the standard output, e.g.:

            python3 dinic_maxflow.py --summary < input.txt

        This does not alter the stdin format or the original output
        lines in any way; it only appends extra lines when requested.
    """
    args = sys.argv[1:]
    include_summary = "--summary" in args

    data = sys.stdin.read().split()
    if not data:
        return
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

    edges_in = []
    for _ in range(m):
        u = next_int()
        v = next_int()
        cap = next_int()
        edges_in.append((u, v, cap))

    if include_summary:
        max_flow_value, flows, summary = solve(n, edges_in, s, t, include_summary=True)
    else:
        max_flow_value, flows = solve(n, edges_in, s, t, include_summary=False)
        summary = None

    out_lines = [str(max_flow_value)]
    out_lines.extend(str(f) for f in flows)

    if summary is not None:
        out_lines.append("OPERATION_SUMMARY:")
        for key in (
            "bfs_phases",
            "augmenting_paths_found",
            "edges_saturated",
            "dead_ends_pruned",
            "total_major_operations",
        ):
            out_lines.append(f"{key}={summary[key]}")

    sys.stdout.write("\n".join(out_lines) + "\n")


if __name__ == "__main__":
    main()