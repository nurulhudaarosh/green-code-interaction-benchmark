import sys
from collections import deque


def max_flow(n, edges, s, t, include_operation_summary=False):
    """
    Maximum s-t flow via Dinic's blocking-flow algorithm.

    n     : number of nodes (0 .. n-1)
    edges : list of (u, v, cap) in ORIGINAL order
    s, t  : source and sink
    include_operation_summary : opt-in deterministic summary dict

    Returns:
        (max_flow_value, flows_per_original_edge)
        or (max_flow_value, flows_per_original_edge, operation_summary)

    Guarantees:
      - Deterministic tie handling: adjacency lists in insertion order,
        lowest-index eligible residual arc consumed first.
      - Original edge order preserved: flows[i] corresponds to edges[i].
      - Zero-capacity, self-loop, and parallel edges all reported correctly.
      - Standard library only; no randomness, no external services.
    """
    m = len(edges)

    # ---- Boundary B1 / B3: no edges -----------------------------------
    if m == 0:
        flows = []
        if not include_operation_summary:
            return 0, flows
        return 0, flows, {
            "bfs_phases": 0, "dfs_augmentations": 0,
            "edge_scans": 0, "total_operations": 0,
        }

    # ---- Boundary B2: source equals sink ------------------------------
    if s == t:
        flows = [0] * m
        if not include_operation_summary:
            return 0, flows
        return 0, flows, {
            "bfs_phases": 0, "dfs_augmentations": 0,
            "edge_scans": 0, "total_operations": 0,
        }

    # ---- Residual graph: forward/reverse arcs inserted ADJACENTLY -----
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

    # ---- Boundary B7: INF must exceed total possible push -------------
    total_cap = sum(c for (_, _, c) in edges)
    INF = total_cap + 1  # exact integer > any augmenting amount

    # ---- Boundary B11: deep chains need higher recursion limit --------
    sys.setrecursionlimit(max(10_000, 4 * (n + m) + 100))

    # ---- Deterministic operation counters -----------------------------
    bfs_phases        = 0
    dfs_augmentations = 0
    edge_scans        = 0

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
                v = to[eid]
                if cap[eid] > 0 and level[v] < 0:
                    level[v] = level[u] + 1
                    q.append(v)
        return level[t] >= 0

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
            it[u] += 1
            edge_scans += 1
        return 0

    while bfs():
        bfs_phases += 1
        for i in range(n):
            it[i] = 0
        while True:
            pushed = dfs(s, INF)
            if pushed == 0:
                break
            dfs_augmentations += 1
            flow_value += pushed

    # ---- Flow recovery: flow on original edge i = residual on 2*i+1 ---
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


# ============================== TESTS ==================================
if __name__ == "__main__":
    # ---- Default call: original 2-tuple, order preserved --------------
    edges = [(0, 1, 16), (0, 2, 13), (1, 2, 10), (2, 1, 4),
             (1, 3, 12), (3, 2, 9), (2, 4, 14), (4, 3, 7),
             (3, 5, 20), (4, 5, 4)]
    val, flows = max_flow(6, edges, 0, 5)
    assert val == 23 and len(flows) == len(edges), (val, flows)
    print("CLRS example:", val, flows)

    # ---- Opt-in summary ----------------------------------------------
    val, flows, summary = max_flow(6, edges, 0, 5,
                                   include_operation_summary=True)
    assert set(summary) == {"bfs_phases", "dfs_augmentations",
                            "edge_scans", "total_operations"}
    assert summary["total_operations"] == (
        summary["bfs_phases"] + summary["dfs_augmentations"]
        + summary["edge_scans"])
    print("With summary:", val, flows, summary)

    # ---- Determinism -------------------------------------------------
    r1 = max_flow(6, edges, 0, 5, include_operation_summary=True)
    r2 = max_flow(6, edges, 0, 5, include_operation_summary=True)
    assert r1 == r2
    print("Determinism ok")

    # ---- B1: empty edge list -----------------------------------------
    v, f = max_flow(3, [], 0, 2)
    assert (v, f) == (0, [])
    v, f, s = max_flow(3, [], 0, 2, include_operation_summary=True)
    assert s["total_operations"] == 0 and f == []
    print("B1  ok:", (v, f, s))

    # ---- B2: s == t ---------------------------------------------------
    v, f = max_flow(4, [(0, 1, 5), (1, 3, 5)], 2, 2)
    assert v == 0 and f == [0, 0]
    print("B2  ok:", (v, f))

    # ---- B3: n == 1, s == t == 0 --------------------------------------
    v, f = max_flow(1, [], 0, 0)
    assert (v, f) == (0, [])
    print("B3  ok:", (v, f))

    # ---- B4: all capacities zero --------------------------------------
    v, f = max_flow(4, [(0, 1, 0), (1, 3, 0), (0, 2, 0), (2, 3, 0)], 0, 3)
    assert v == 0 and f == [0, 0, 0, 0]
    print("B4  ok:", (v, f))

    # ---- B5: self-loop must not corrupt other indices -----------------
    v, f = max_flow(3, [(0, 0, 7), (0, 1, 4), (1, 2, 4)], 0, 2)
    assert v == 4 and f == [0, 4, 4]
    print("B5  ok:", (v, f))

    # ---- B6: parallel edges keep their own flows in order -------------
    v, f = max_flow(3, [(0, 1, 2), (0, 1, 3), (1, 2, 5)], 0, 2)
    assert v == 5 and sum(f[:2]) == 5 and f[2] == 5
    print("B6  ok:", (v, f))

    # ---- B7: very large capacities ------------------------------------
    BIG = 10**18
    v, f = max_flow(3, [(0, 1, BIG), (1, 2, BIG)], 0, 2)
    assert v == BIG and f == [BIG, BIG]
    print("B7  ok:", (v, f))

    # ---- B8: sparse graph, sink label = n-1 ---------------------------
    v, f = max_flow(1000, [(0, 999, 3)], 0, 999)
    assert v == 3 and f == [3]
    print("B8  ok:", (v, f))

    # ---- B9: source with no outgoing capacity -------------------------
    v, f = max_flow(3, [(0, 1, 0), (1, 2, 5)], 0, 2)
    assert v == 0 and f == [0, 0]
    print("B9  ok:", (v, f))

    # ---- B10: sink with no incoming capacity --------------------------
    v, f = max_flow(3, [(0, 1, 5), (1, 2, 0)], 0, 2)
    assert v == 0 and f == [0, 0]
    print("B10 ok:", (v, f))

    # ---- B11: long chain (deep recursion) -----------------------------
    N = 5000
    chain = [(i, i + 1, 1) for i in range(N - 1)]
    v, f = max_flow(N, chain, 0, N - 1)
    assert v == 1 and f == [1] * (N - 1)
    print("B11 ok:", v, "chain length", N)

    # ---- B12: isolated s and t (no incident edges) --------------------
    v, f = max_flow(5, [(1, 2, 9)], 0, 4)
    assert v == 0 and f == [0]
    print("B12 ok:", (v, f))

    # ---- B13: duplicate self-loops interleaved with normal edges ------
    edges = [(0, 0, 3), (0, 1, 5), (0, 0, 3), (1, 2, 5), (2, 2, 3)]
    v, f = max_flow(3, edges, 0, 2)
    assert v == 5 and f == [0, 5, 0, 5, 0]
    print("B13 ok:", (v, f))

    # ---- B14: non-contiguous labels with isolated interior nodes ------
    v, f = max_flow(10, [(0, 1, 4), (1, 9, 4)], 0, 9)
    assert v == 4 and f == [4, 4]
    print("B14 ok:", (v, f))

    # ---- Determinism + summary invariants across boundary shapes ------
    for label, args in [
        ("B1", (3, [], 0, 2)),
        ("B5", (3, [(0, 0, 7), (0, 1, 4), (1, 2, 4)], 0, 2)),
        ("B7", (3, [(0, 1, 10**18), (1, 2, 10**18)], 0, 2)),
    ]:
        a = max_flow(*args, include_operation_summary=True)
        b = max_flow(*args, include_operation_summary=True)
        assert a == b, (label, a, b)
        assert a[2]["total_operations"] == (
            a[2]["bfs_phases"] + a[2]["dfs_augmentations"]
            + a[2]["edge_scans"])
    print("Determinism + summary invariants ok")
    print("ALL TESTS PASSED")