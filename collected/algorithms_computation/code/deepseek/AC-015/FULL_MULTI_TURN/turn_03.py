import sys
from collections import deque

def max_flow(n, edges, s, t, include_operation_summary=False):
    """
    n     : number of nodes (0 .. n-1)
    edges : list of (u, v, cap) in ORIGINAL order
    s, t  : source and sink
    include_operation_summary : if True, append an operation_summary dict
                                to the return tuple.

    Returns:
        (max_flow_value, flows_per_original_edge)
        or, if include_operation_summary=True,
        (max_flow_value, flows_per_original_edge, operation_summary)

    operation_summary is a deterministic dict with keys:
        bfs_phases, dfs_augmentations, edge_scans, total_operations
    """
    m = len(edges)

    # ---- Residual graph: forward/reverse arcs inserted ADJACENTLY ----
    # For original edge i: forward arc = 2*i, reverse arc = 2*i + 1.
    to    = [0] * (2 * m)
    cap   = [0] * (2 * m)
    graph = [[] for _ in range(n)]

    for i, (u, v, c) in enumerate(edges):
        fwd = 2 * i
        rev = 2 * i + 1
        to[fwd], cap[fwd] = v, c
        to[rev], cap[rev] = u, 0
        graph[u].append(fwd)   # insertion order preserved
        graph[v].append(rev)   # insertion order preserved

    # ---- Deterministic operation counters ----------------------------
    bfs_phases        = 0
    dfs_augmentations = 0
    edge_scans        = 0

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
        nonlocal edge_scans
        if u == t:
            return pushed
        while it[u] < len(graph[u]):
            eid = graph[u][it[u]]         # deterministic: lowest index first
            v = to[eid]
            if cap[eid] > 0 and level[v] == level[u] + 1:
                d = dfs(v, min(pushed, cap[eid]))
                if d > 0:
                    cap[eid]     -= d
                    cap[eid ^ 1] += d     # paired adjacent arcs
                    return d
            it[u] += 1                    # current-arc advanced -> a scan
            edge_scans += 1
        return 0

    INF = float('inf')
    while bfs():
        bfs_phases += 1                   # a successful phase was started
        for i in range(n):
            it[i] = 0
        while True:
            pushed = dfs(s, INF)
            if pushed == 0:
                break
            dfs_augmentations += 1        # a positive augmentation occurred
            flow_value += pushed

    # ---- Flow recovery: flow on original edge i is the residual on
    #      its reverse arc (index 2*i + 1). Correct because arcs are paired.
    flows = [cap[2 * i + 1] for i in range(m)]

    if not include_operation_summary:
        return flow_value, flows

    operation_summary = {
        "bfs_phases":        bfs_phases,
        "dfs_augmentations": dfs_augmentations,
        "edge_scans":        edge_scans,
        "total_operations":  bfs_phases + dfs_augmentations + edge_scans,
    }
    return flow_value, flows, operation_summary


# ----------------------------- Self-tests ------------------------------
if __name__ == "__main__":
    # --- Backwards compatibility: default call returns the original 2-tuple
    edges = [(0, 1, 5), (0, 2, 5), (1, 3, 5), (2, 3, 5)]
    out = max_flow(4, edges, 0, 3)
    assert isinstance(out, tuple) and len(out) == 2
    val, flows = out
    assert val == 10 and flows == [5, 5, 5, 5], out
    print("Default (2-tuple):", out)

    # --- Opt-in: 3-tuple with operation_summary
    val, flows, summary = max_flow(4, edges, 0, 3,
                                   include_operation_summary=True)
    assert val == 10 and flows == [5, 5, 5, 5]
    assert set(summary) == {"bfs_phases", "dfs_augmentations",
                            "edge_scans", "total_operations"}
    assert summary["total_operations"] == (
        summary["bfs_phases"] + summary["dfs_augmentations"]
        + summary["edge_scans"])
    print("With summary:", val, flows, summary)

    # --- Determinism: same input -> identical summary
    val2, flows2, summary2 = max_flow(4, edges, 0, 3,
                                      include_operation_summary=True)
    assert (val2, flows2, summary2) == (val, flows, summary)
    print("Deterministic:", (val2, flows2, summary2) == (val, flows, summary))

    # --- Zero-capacity and self-loop edges still reported, order preserved
    edges = [(0, 0, 7), (0, 1, 4), (1, 2, 4)]
    val, flows, summary = max_flow(3, edges, 0, 2,
                                   include_operation_summary=True)
    assert val == 4 and flows == [0, 4, 4]
    assert len(flows) == len(edges)
    print("Edge-order + summary:", val, flows, summary)