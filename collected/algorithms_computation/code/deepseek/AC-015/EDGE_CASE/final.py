import sys
from collections import deque


class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]
        # Each entry: [to, cap, rev_index, orig_id]
        #   orig_id = -1 for reverse (residual) edges
        #   orig_id >= 0 for forward edges mapping to input edge index
        self.orig_caps = []
        self.orig_from = []

    def add_edge(self, u, v, cap, orig_id):
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
            for to, cap, _rev, _oid in self.graph[u]:
                if cap > 0 and self.level[to] < 0:
                    self.level[to] = self.level[u] + 1
                    q.append(to)
        return self.level[t] >= 0

    def dfs(self, u, t, f):
        if u == t:
            return f
        while self.iter[u] < len(self.graph[u]):
            e = self.graph[u][self.iter[u]]
            to, cap, rev, _oid = e
            if cap > 0 and self.level[to] == self.level[u] + 1:
                d = self.dfs(to, t, min(f, cap))
                if d > 0:
                    e[1] -= d
                    self.graph[to][rev][1] += d
                    return d
            self.iter[u] += 1
        return 0

    def max_flow(self, s, t, inf):
        flow = 0
        while self.bfs(s, t):
            self.iter = [0] * self.n
            while True:
                f = self.dfs(s, t, inf)
                if f == 0:
                    break
                flow += f
        return flow


def solve(n, edges, s, t):
    """
    n: number of vertices
    edges: list of (u, v, capacity), input order preserved
    s, t: source, sink
    Returns (max_flow_value, [flow_per_edge_in_input_order])

    Handles boundary cases:
      - s == t  -> (0, zeros)
      - m == 0  -> (0, [])
      - zero-capacity, self-loop, parallel, anti-parallel edges
      - huge capacities (Python big ints)
    """
    m = len(edges)

    # B11 / B3 / B1 / B2: trivial cases
    if m == 0 or s == t:
        return 0, [0] * m

    # B13: DFS depth bounded by n
    sys.setrecursionlimit(max(2000, 2 * n + 10))

    # B5 / B14: INF strictly greater than total capacity so a single DFS
    # can saturate any augmenting path in one shot.
    total_cap = sum(c for _u, _v, c in edges)
    INF = total_cap + 1 if total_cap > 0 else 1

    din = Dinic(n)
    for idx, (u, v, cap) in enumerate(edges):
        # B12: defensive range check (input spec assumes valid; we fail loudly)
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"Edge {idx} endpoint out of range: ({u},{v}) for n={n}")
        din.add_edge(u, v, cap, idx)
        din.orig_caps.append(cap)
        din.orig_from.append(u)

    maxflow = din.max_flow(s, t, INF)

    # Recover flow per original edge in input order.
    result = [0] * m
    # Build a lookup: for each u, list of (orig_id, forward_edge_obj)
    by_origin = [[] for _ in range(n)]
    for u in range(n):
        for e in din.graph[u]:
            if e[3] >= 0:  # forward (original) edge
                by_origin[u].append((e[3], e))
    for idx in range(m):
        u = din.orig_from[idx]
        for oid, e in by_origin[u]:
            if oid == idx:
                # B4 / B6: zero-cap or self-loop naturally yield 0 here
                result[idx] = din.orig_caps[idx] - e[1]
                break

    # B9 / B10: if s unreachable from t, maxflow == 0 and every flow is 0
    # (already reflected in `result`).
    return maxflow, result


def main():
    data = sys.stdin.buffer.read().split()
    if not data:  # B11
        return
    it = iter(data)
    try:
        n = int(next(it))
        m = int(next(it))
        s = int(next(it))
        t = int(next(it))
    except StopIteration:
        return

    edges = []
    for _ in range(m):
        try:
            u = int(next(it)); v = int(next(it)); c = int(next(it))
        except StopIteration:
            break  # truncated input; process what we have
        edges.append((u, v, c))

    maxflow, flows = solve(n, edges, s, t)
    out = [str(maxflow)]
    out.extend(str(f) for f in flows)
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()