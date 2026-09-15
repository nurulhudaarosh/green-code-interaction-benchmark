import sys
from collections import deque

def max_flow(n, edges, s, t):
    """
    n     : number of nodes (0 .. n-1)
    edges : list of (u, v, cap) in ORIGINAL order
    s, t  : source and sink
    returns: (max_flow_value, flows_per_original_edge)
    Deterministic: adjacency lists are in insertion order; DFS consumes
    the smallest-index eligible residual arc first.
    """
    m = len(edges)

    # ---- Residual graph: forward/reverse arcs inserted ADJACENTLY ----
    # For original edge i: forward arc index = 2*i, reverse = 2*i + 1.
    to      = [0] * (2 * m)
    cap     = [0] * (2 * m)
    graph   = [[] for _ in range(n)]

    for i, (u, v, c) in enumerate(edges):
        fwd = 2 * i
        rev = 2 * i + 1
        to[fwd], cap[fwd] = v, c
        to[rev], cap[rev] = u, 0
        graph[u].append(fwd)   # insertion order preserved
        graph[v].append(rev)   # insertion order preserved

    # ---- Dinic's algorithm -------------------------------------------
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
                v = to[eid]
                if cap[eid] > 0 and level[v] < 0:
                    level[v] = level[u] + 1
                    q.append(v)
        return level[t] >= 0

    sys.setrecursionlimit(1_000_000)

    def dfs(u, pushed):
        if u == t:
            return pushed
        while it[u] < len(graph[u]):
            eid = graph[u][it[u]]          # deterministic: lowest index first
            v = to[eid]
            if cap[eid] > 0 and level[v] == level[u] + 1:
                d = dfs(v, min(pushed, cap[eid]))
                if d > 0:
                    cap[eid]     -= d
                    cap[eid ^ 1] += d      # paired adjacent arcs
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

    # ---- Flow recovery: flow on original edge i = residual on its reverse
    #      arc (index 2*i + 1). Correct because forward/reverse are paired.
    flows = [cap[2 * i + 1] for i in range(m)]
    return flow_value, flows


# ----------------------------- Self-test ------------------------------
if __name__ == "__main__":
    # Defect demo network
    edges = [(0, 1, 5), (0, 2, 5), (1, 3, 5), (2, 3, 5)]
    val, flows = max_flow(4, edges, 0, 3)
    assert val == 10, val
    assert flows == [5, 5, 5, 5], flows
    print("Demo 1:", val, flows)

    # Zero-capacity edge must still be reported
    edges = [(0, 1, 0), (0, 2, 3), (2, 1, 3), (1, 3, 3)]
    val, flows = max_flow(4, edges, 0, 3)
    assert flows[0] == 0 and len(flows) == len(edges)
    print("Demo 2:", val, flows)

    # Parallel edges: each must carry its own reported flow
    edges = [(0, 1, 2), (0, 1, 3), (1, 2, 5)]
    val, flows = max_flow(3, edges, 0, 2)
    assert val == 5
    assert sum(flows[:2]) == 5 and flows[2] == 5
    print("Demo 3:", val, flows)

    # Self-loop must report 0 and not corrupt other indices
    edges = [(0, 0, 7), (0, 1, 4), (1, 2, 4)]
    val, flows = max_flow(3, edges, 0, 2)
    assert val == 4 and flows == [0, 4, 4], flows
    print("Demo 4:", val, flows)