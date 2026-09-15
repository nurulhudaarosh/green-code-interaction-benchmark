"""
PROBLEM UNDERSTANDING
======================
Given: a directed capacitated network G = (V, E) with a source s and a sink t.
Each directed edge e has a non-negative integer (or numeric) capacity c(e).
Multiple edges between the same pair of nodes (parallel edges) may exist, and
self-loops / edges into s or out of t may appear.

Goal: compute the value of the maximum flow from s to t, and report the flow
sent on each ORIGINAL edge (in the same order the edges were given as input).

KEY CONSTRAINTS
================
1. Flow conservation: for every vertex v != s, t, total flow in = total flow out.
2. Capacity constraint: 0 <= flow(e) <= capacity(e) for every original edge e.
3. Skew symmetry / no flow on reverse residual arcs is reported — only the
   original edges' flow values are output.
4. The graph may contain parallel edges and must be handled without merging
   them (each keeps its own residual capacity and its own reported flow).
5. Must be deterministic: same input -> same output, every run (no randomness,
   no dependence on hash/set iteration order, no external I/O).

REQUIRED OUTPUT
================
- The maximum flow value (a single number).
- A list of flows, one per original input edge, in the original input order
  (each 0 <= flow(e) <= capacity(e)).

ALGORITHM (Dinic's Blocking Flow)
===================================
Dinic's algorithm computes max flow in phases:
1. Build a level graph from s via BFS on residual capacities (edges with
   residual capacity > 0). If t is unreachable, stop — current flow is max.
2. Find a blocking flow in the level graph using DFS with the "current arc"
   optimization (iterator pointers per vertex to avoid re-scanning dead arcs).
3. Augment the flow using the blocking flow found, update residual capacities.
4. Repeat from step 1.

Complexity: O(V^2 * E) in general graphs, O(E * sqrt(V)) on unit-capacity /
bipartite-matching-like graphs. Runs to completion deterministically because
adjacency lists are stored in fixed (insertion) order and BFS/DFS use them
in that fixed order — no sets, no dict iteration over unordered structures
affecting results, no randomness.

To recover per-original-edge flow, each original edge is added to the
residual graph as a forward arc (capacity c, paired reverse arc capacity 0).
We remember the index of the forward arc for each original edge; at the end,
flow(e) = capacity_original(e) - current_residual_capacity(forward_arc).
"""

from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]  # graph[u] = list of arc indices
        self.edge_to = []      # edge_to[arc] = destination vertex
        self.edge_cap = []     # edge_cap[arc] = residual capacity

    def add_edge(self, u, v, cap):
        """Add directed edge u->v with capacity cap. Returns the arc index
        of the forward arc (used later to recover flow on original edges)."""
        fwd = len(self.edge_to)
        self.edge_to.append(v)
        self.edge_cap.append(cap)
        self.graph[u].append(fwd)

        rev = len(self.edge_to)
        self.edge_to.append(u)
        self.edge_cap.append(0)
        self.graph[v].append(rev)

        return fwd

    def _bfs_levels(self, s, t):
        level = [-1] * self.n
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for arc in self.graph[u]:
                v = self.edge_to[arc]
                if self.edge_cap[arc] > 0 and level[v] == -1:
                    level[v] = level[u] + 1
                    q.append(v)
        return level if level[t] != -1 else None

    def _dfs_blocking(self, u, t, pushed, level, it):
        if u == t:
            return pushed
        while it[u] < len(self.graph[u]):
            arc = self.graph[u][it[u]]
            v = self.edge_to[arc]
            if self.edge_cap[arc] > 0 and level[v] == level[u] + 1:
                d = self._dfs_blocking(v, t, min(pushed, self.edge_cap[arc]), level, it)
                if d > 0:
                    self.edge_cap[arc] -= d
                    self.edge_cap[arc ^ 1] += d
                    return d
            it[u] += 1
        return 0

    def max_flow(self, s, t):
        flow = 0
        INF = float('inf')
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


def solve(n, s, t, edges):
    """
    n:     number of vertices, labeled 0..n-1
    s, t:  source and sink vertex indices
    edges: list of (u, v, capacity), in the exact order they should be
           reported back (original edge order preserved)

    Returns: (max_flow_value, flows) where flows[i] is the flow sent on
              edges[i], in the SAME order as the input list.
    """
    dinic = Dinic(n)
    forward_arc_index = []
    for (u, v, cap) in edges:
        arc = dinic.add_edge(u, v, cap)
        forward_arc_index.append(arc)

    max_flow_value = dinic.max_flow(s, t)

    flows = []
    for (u, v, cap), arc in zip(edges, forward_arc_index):
        used = cap - dinic.edge_cap[arc]   # capacity consumed on this arc
        flows.append(used)

    return max_flow_value, flows


def _demo():
    # Classic textbook example:
    # vertices: 0=s, 1, 2, 3, 4, 5=t
    n = 6
    s, t = 0, 5
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

    max_flow_value, flows = solve(n, s, t, edges)

    print("Max flow:", max_flow_value)
    print("Flow on each original edge (in input order):")
    for (u, v, cap), f in zip(edges, flows):
        print(f"  {u} -> {v}  capacity={cap:>3}  flow={f:>3}")


if __name__ == "__main__":
    _demo()