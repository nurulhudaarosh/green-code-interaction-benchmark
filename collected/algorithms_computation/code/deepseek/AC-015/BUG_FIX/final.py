import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        # Each entry: [to, remaining_cap, index_of_reverse_edge]
        self.graph = [[] for _ in range(n)]
        # For each original edge i, store a direct reference to its forward slot
        # as (u, forward_slot). Stable regardless of later insertions or
        # any reordering of self.graph.
        self.forward_refs = []
        # Original capacities, indexed by original edge order.
        self.original_caps = []

    def add_edge(self, u, v, cap):
        """Add original directed edge u->v with capacity cap."""
        fwd_idx = len(self.graph[u])
        rev_idx = len(self.graph[v])
        # Forward slot
        self.graph[u].append([v, cap, rev_idx])
        # Reverse slot (residual)
        self.graph[v].append([u, 0, fwd_idx])
        # Record a stable reference to the forward slot, in original order.
        self.forward_refs.append((u, fwd_idx))
        self.original_caps.append(cap)

    def bfs(self, s, t):
        """Build level graph. Deterministic: adjacency scanned in insertion order."""
        self.level = [-1] * self.n
        self.level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v, cap, _ in self.graph[u]:
                if cap > 0 and self.level[v] == -1:
                    self.level[v] = self.level[u] + 1
                    q.append(v)
        return self.level[t] != -1

    def dfs(self, u, t, pushed):
        """Blocking-flow DFS. Deterministic: current-arc `it` advances monotonically."""
        if u == t:
            return pushed
        while self.it[u] < len(self.graph[u]):
            edge = self.graph[u][self.it[u]]
            v, cap, rev = edge
            if cap > 0 and self.level[v] == self.level[u] + 1:
                d = self.dfs(v, t, pushed if pushed < cap else cap)
                if d > 0:
                    edge[1] -= d
                    self.graph[v][rev][1] += d
                    return d
            self.it[u] += 1
        return 0

    def max_flow(self, s, t):
        flow = 0
        while self.bfs(s, t):
            self.it = [0] * self.n
            while True:
                pushed = self.dfs(s, t, float('inf'))
                if pushed == 0:
                    break
                flow += pushed
        return flow

    def edge_flows_in_order(self):
        """Return flow on each original edge, in original insertion order.

        Uses stored forward-slot references, so the result is correct even if
        self.graph adjacency is reordered, and is deterministic by construction.
        """
        flows = []
        for i, (u, fwd_idx) in enumerate(self.forward_refs):
            remaining = self.graph[u][fwd_idx][1]
            flows.append(self.original_caps[i] - remaining)
        return flows


def solve_max_flow(n, s, t, edges):
    dinic = Dinic(n)
    for u, v, cap in edges:
        dinic.add_edge(u, v, cap)
    value = dinic.max_flow(s, t)
    return value, dinic.edge_flows_in_order()


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    idx = 0
    n = int(data[idx]); idx += 1
    m = int(data[idx]); idx += 1
    s = int(data[idx]); idx += 1
    t = int(data[idx]); idx += 1
    edges = []
    for _ in range(m):
        u = int(data[idx]); idx += 1
        v = int(data[idx]); idx += 1
        c = int(data[idx]); idx += 1
        edges.append((u, v, c))
    value, flows = solve_max_flow(n, s, t, edges)
    out = [str(value)]
    out.extend(str(f) for f in flows)
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()