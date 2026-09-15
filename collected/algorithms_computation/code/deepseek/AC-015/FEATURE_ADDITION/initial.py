import sys
from collections import deque

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    it = iter(data)
    n = int(next(it))
    m = int(next(it))
    s = int(next(it))
    t = int(next(it))

    # Edge list in residual form: to[], cap[], next index is i^1
    to = []
    cap = []
    # head[v] = index of first residual arc out of v (linked-list style)
    head = [-1] * n
    # We'll store (to, cap) pairs; reverse arc is i^1

    def add_edge(u, v, c):
        # forward arc
        to.append(v)
        cap.append(c)
        to.append(u)
        cap.append(0)

    # Record original edges for output
    orig_u = []
    orig_v = []
    orig_cap = []
    orig_arc_index = []  # forward arc index for each original edge

    # Build adjacency via lists of arc indices
    adj = [[] for _ in range(n)]

    for _ in range(m):
        u = int(next(it))
        v = int(next(it))
        c = int(next(it))
        orig_u.append(u)
        orig_v.append(v)
        orig_cap.append(c)
        fwd_idx = len(to)
        orig_arc_index.append(fwd_idx)
        add_edge(u, v, c)
        adj[u].append(fwd_idx)
        adj[v].append(fwd_idx ^ 1)

    # Dinic's algorithm
    INF = float('inf')
    level = [-1] * n
    iter_ptr = [0] * n

    def bfs():
        for i in range(n):
            level[i] = -1
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for eid in adj[u]:
                if cap[eid] > 0 and level[to[eid]] < 0:
                    level[to[eid]] = level[u] + 1
                    q.append(to[eid])
        return level[t] >= 0

    def dfs(u, f):
        if u == t:
            return f
        while iter_ptr[u] < len(adj[u]):
            eid = adj[u][iter_ptr[u]]
            v = to[eid]
            if cap[eid] > 0 and level[v] == level[u] + 1:
                d = dfs(v, f if f < cap[eid] else cap[eid])
                if d > 0:
                    cap[eid] -= d
                    cap[eid ^ 1] += d
                    return d
            iter_ptr[u] += 1
        return 0

    max_flow = 0
    while bfs():
        for i in range(n):
            iter_ptr[i] = 0
        while True:
            f = dfs(s, INF)
            if f == 0:
                break
            max_flow += f

    # Output
    out = [str(max_flow)]
    for i in range(m):
        fwd = orig_arc_index[i]
        flow_val = orig_cap[i] - cap[fwd]
        out.append(str(flow_val))
    sys.stdout.write("\n".join(out) + "\n")

if __name__ == "__main__":
    main()