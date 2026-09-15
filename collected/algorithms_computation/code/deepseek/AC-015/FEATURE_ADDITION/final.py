import sys
from collections import deque


def max_flow_planner(n, m, s, t, edges, include_operation_summary=False):
    """
    Compute max s-t flow using Dinic's algorithm.

    Parameters
    ----------
    n : int                     number of nodes
    m : int                     number of original edges
    s : int                     source node
    t : int                     sink node
    edges : list of (u, v, c)   original edges, in original order
    include_operation_summary : bool
        If False (default), returns the original result only:
            {"max_flow": int, "flows": [int]*m}
        If True, additionally returns:
            {"operation_summary": {...}}

    Returns
    -------
    dict
        Original fields always present. operation_summary added only when
        include_operation_summary is True.
    """
    # ---- Build residual graph -------------------------------------------
    to = []
    cap = []
    adj = [[] for _ in range(n)]

    def add_edge(u, v, c):
        to.append(v); cap.append(c)
        to.append(u); cap.append(0)

    orig_cap = []
    orig_arc_index = []

    for (u, v, c) in edges:
        orig_cap.append(c)
        fwd_idx = len(to)
        orig_arc_index.append(fwd_idx)
        add_edge(u, v, c)
        adj[u].append(fwd_idx)
        adj[v].append(fwd_idx ^ 1)

    # ---- Dinic's algorithm with counters --------------------------------
    INF = float('inf')
    level = [-1] * n
    iter_ptr = [0] * n

    # operation counters (deterministic)
    bfs_phases = 0
    successful_augmentations = 0
    failed_dfs_probes = 0

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
        nonlocal successful_augmentations, failed_dfs_probes
        if u == t:
            successful_augmentations += 1
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
        # Reached here => this DFS branch produced no flow.
        failed_dfs_probes += 1
        return 0

    max_flow = 0
    while True:
        bfs_phases += 1
        if not bfs():
            break
        for i in range(n):
            iter_ptr[i] = 0
        while True:
            f = dfs(s, INF)
            if f == 0:
                break
            max_flow += f

    # ---- Recover original edge flows ------------------------------------
    flows = []
    for i in range(m):
        fwd = orig_arc_index[i]
        flows.append(orig_cap[i] - cap[fwd])

    # ---- Assemble result (original fields unchanged) --------------------
    result = {
        "max_flow": max_flow,
        "flows": flows,
    }

    if include_operation_summary:
        result["operation_summary"] = {
            "bfs_phases": bfs_phases,
            "successful_augmentations": successful_augmentations,
            "failed_dfs_probes": failed_dfs_probes,
            "total_major_operations": (
                bfs_phases + successful_augmentations + failed_dfs_probes
            ),
        }

    return result


# ---- CLI wrapper (preserves original textual output exactly) ------------
def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    it = iter(data)
    n = int(next(it)); m = int(next(it))
    s = int(next(it)); t = int(next(it))
    edges = []
    for _ in range(m):
        u = int(next(it)); v = int(next(it)); c = int(next(it))
        edges.append((u, v, c))

    # Feature flag: set to True only when the caller explicitly requests it.
    include_operation_summary = False

    res = max_flow_planner(n, m, s, t, edges,
                           include_operation_summary=include_operation_summary)

    # Original textual output (unchanged when feature disabled)
    lines = [str(res["max_flow"])]
    lines.extend(str(f) for f in res["flows"])
    if include_operation_summary:
        op = res["operation_summary"]
        lines.append(f"operation_summary bfs_phases={op['bfs_phases']} "
                     f"successful_augmentations={op['successful_augmentations']} "
                     f"failed_dfs_probes={op['failed_dfs_probes']} "
                     f"total_major_operations={op['total_major_operations']}")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()