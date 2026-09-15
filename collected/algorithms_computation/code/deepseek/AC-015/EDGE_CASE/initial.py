import sys
from collections import deque

INF = float('inf')


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]
        # Each entry: [to, cap, rev_index, orig_edge_id]
        # orig_edge_id = -1 for reverse edges, >= 0 for forward edges
        self.orig_caps = []   # capacity of each original edge
        self.orig_edges = []  # (u, v, edge_ref) for each original edge

    def add_edge(self, u, v, cap, orig_id):
        """Add an original edge u->v with capacity cap and id orig_id."""
        fwd = [v, cap, len(self.graph[v]), orig_id]
        rev = [u, 0,   len(self.graph[u]), -1]
        self.graph[u].append(fwd)
        self.graph[v].append(rev)

    def bfs(self, s, t):
        self.level = [-1] * self.n
        self.level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for to, cap, rev, _ in self.graph[u]:
                if cap > 0 and self.level[to] < 0:
                    self.level[to] = self.level[u] + 1
                    q.append(to)
        return self.level[t] >= 0

    def dfs(self, u, t, f):
        if u == t:
            return f
        while self.iter[u] < len(self.graph[u]):
            e = self.graph[u][self.iter[u]]
            to, cap, rev, _ = e
            if cap > 0 and self.level[to] == self.level[u] + 1:
                d = self.dfs(to, t, min(f, cap))
                if d > 0:
                    e[1] -= d
                    self.graph[to][rev][1] += d
                    return d
            self.iter[u] += 1
        return 0

    def max_flow(self, s, t):
        flow = 0
        while self.bfs(s, t):
            self.iter = [0] * self.n
            while True:
                f = self.dfs(s, t, INF)
                if f == 0:
                    break
                flow += f
        return flow


def solve(n, edges, s, t):
    """
    n: number of vertices (0-indexed)
    edges: list of (u, v, capacity)
    s, t: source and sink
    Returns: (max_flow_value, [flow_on_each_original_edge_in_order])
    """
    din = Dinic(n)
    for idx, (u, v, cap) in enumerate(edges):
        din.add_edge(u, v, cap, idx)
        din.orig_caps.append(cap)
        din.orig_edges.append((u, v))

    maxflow = din.max_flow(s, t)

    # Recover flow on each original edge: flow = capacity - remaining_residual_capacity
    result = []
    for idx in range(len(edges)):
        u = din.orig_edges[idx][0]
        # Find the forward edge object with orig_id == idx
        found = None
        for e in din.graph[u]:
            if e[3] == idx:
                found = e
                break
        assert found is not None, f"Original edge {idx} not found"
        remaining = found[1]
        result.append(din.orig_caps[idx] - remaining)

    return maxflow, result


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    it = iter(data)
    n = int(next(it))
    m = int(next(it))
    s = int(next(it))
    t = int(next(it))
    edges = []
    for _ in range(m):
        u = int(next(it))
        v = int(next(it))
        c = int(next(it))
        edges.append((u, v, c))

    maxflow, flows = solve(n, edges, s, t)
    print(maxflow)
    for f in flows:
        print(f)


if __name__ == "__main__":
    main()