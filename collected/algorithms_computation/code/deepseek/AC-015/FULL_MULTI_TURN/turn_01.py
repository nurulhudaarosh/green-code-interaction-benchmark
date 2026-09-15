import sys
from collections import deque

def max_flow(n, edges, s, t):
    """
    n     : number of nodes (0 .. n-1)
    edges : list of (u, v, cap) in ORIGINAL order
    s, t  : source and sink
    returns: (max_flow_value, list_of_flows_per_original_edge)
    """
    # ---- Build residual graph with paired edges -----------------------
    # For each original edge i: forward arc = 2*i, reverse arc = 2*i+1
    to      = []
    cap     = []          # residual capacity
    orig_id = []          # original edge index (or -1 for reverse arcs)

    graph = [[] for _ in range(n)]

    for i, (u, v, c) in enumerate(edges):
        # forward arc
        graph[u].append(len(to))
        to.append(v); cap.append(c); orig_id.append(i)
        # reverse arc
        graph[v].append(len(to))
        to.append(u); cap.append(0); orig_id.append(i)

    # ---- Dinic's algorithm --------------------------------------------
    flow_value = 0
    level = [-1] * n
    it    = [0]  * n

    def bfs():
        for i in range(n):
            level[i] = -1
        level[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for eid in graph[u]:
                if cap[eid] > 0 and level[to[eid]] < 0:
                    level[to[eid]] = level[u] + 1
                    q.append(to[eid])
        return level[t] >= 0

    sys.setrecursionlimit(1_000_000)

    def dfs(u, pushed):
        if u == t:
            return pushed
        while it[u] < len(graph[u]):
            eid = graph[u][it[u]]
            v = to[eid]
            if cap[eid] > 0 and level[v] == level[u] + 1:
                d = dfs(v, min(pushed, cap[eid]))
                if d > 0:
                    cap[eid] -= d
                    cap[eid ^ 1] += d   # reverse arc is paired via XOR 1
                    return d
            it[u] += 1
        return 0

    INF = float('inf')
    while bfs():
        for i in range(n):
            it[i] = 0
        while True:
            pushed = dfs(s, INF)
            if pushed == 0:
                break
            flow_value += pushed

    # ---- Recover flow on each ORIGINAL edge ---------------------------
    # Flow on forward arc 2*i equals cap[2*i+1] (residual on reverse arc).
    result = [0] * len(edges)
    for i in range(len(edges)):
        result[i] = cap[2 * i + 1]

    return flow_value, result


# --------------------------- Example / self-test -----------------------
if __name__ == "__main__":
    # Classic CLRS-style example
    # Nodes 0..5, s = 0, t = 5
    edges = [
        (0, 1, 16),
        (0, 2, 13),
        (1, 2, 10),
        (2, 1,  4),
        (1, 3, 12),
        (3, 2,  9),
        (2, 4, 14),
        (4, 3,  7),
        (3, 5, 20),
        (4, 5,  4),
    ]
    n, s, t = 6, 0, 5
    val, flows = max_flow(n, edges, s, t)

    print(f"Maximum flow value = {val}")
    print("Flow per original edge (in input order):")
    for (u, v, c), f in zip(edges, flows):
        print(f"  ({u} -> {v}, cap={c}) : flow = {f}")