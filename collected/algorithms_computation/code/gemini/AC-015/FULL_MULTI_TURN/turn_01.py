from collections import deque


class DinicMaxFlow:
    """Computes maximum s-t flow on a directed graph using Dinic's algorithm.

    Preserves original edge index and capacity properties.
    """

    def __init__(self, num_nodes: int):
        self.n = num_nodes
        self.graph = [[] for _ in range(num_nodes)]
        self.edges = []

    def add_edge(self, u: int, v: int, capacity: float) -> int:
        """Adds a directed edge from u to v with specified capacity.

        Returns the original edge index.
        """
        edge_idx = len(self.edges)
        # Forward residual edge
        forward_edge = {
            "u": u,
            "v": v,
            "cap": capacity,
            "flow": 0.0,
            "rev": edge_idx * 2 + 1,
            "is_original": True,
            "orig_idx": edge_idx,
        }
        # Backward residual edge
        backward_edge = {
            "u": v,
            "v": u,
            "cap": 0.0,
            "flow": 0.0,
            "rev": edge_idx * 2,
            "is_original": False,
            "orig_idx": edge_idx,
        }

        self.graph[u].append(len(self.raw_edges))
        self.raw_edges.append(forward_edge)

        self.graph[v].append(len(self.raw_edges))
        self.raw_edges.append(backward_edge)

        self.edges.append(forward_edge)
        return edge_idx

    def _bfs(self, s: int, t: int) -> bool:
        self.level = [-1] * self.n
        self.level[s] = 0
        queue = deque([s])

        while queue:
            u = queue.popleft()
            for edge_id in self.graph[u]:
                edge = self.raw_edges[edge_id]
                if edge["cap"] - edge["flow"] > 1e-9 and self.level[edge["v"]] == -1:
                    self.level[edge["v"]] = self.level[u] + 1
                    queue.append(edge["v"])

        return self.level[t] != -1

    def _dfs(self, u: int, t: int, pushed: float) -> float:
        if pushed <= 0:
            return 0.0
        if u == t:
            return pushed

        for cid in range(self.ptr[u], len(self.graph[u])):
            self.ptr[u] = cid
            edge_id = self.graph[u][cid]
            edge = self.raw_edges[edge_id]
            v = edge["v"]

            if self.level[u] + 1 != self.level[v] or edge["cap"] - edge["flow"] <= 1e-9:
                continue

            tr = self._dfs(v, t, min(pushed, edge["cap"] - edge["flow"]))
            if tr <= 1e-9:
                continue

            edge["flow"] += tr
            self.raw_edges[edge["rev"]]["flow"] -= tr
            return tr

        return 0.0

    def solve(self, s: int, t: int):
        """Calculates the max flow from s to t.

        Returns:
            max_flow (float): Total maximum flow value.
            edge_flows (list): List of flows assigned to each original edge.
        """
        self.raw_edges = []
        # Re-build raw edge list representation
        raw_list = []
        for e in self.edges:
            u, v, cap = e["u"], e["v"], e["cap"]
            f_idx = len(raw_list)
            b_idx = f_idx + 1
            f_edge = {"u": u, "v": v, "cap": cap, "flow": 0.0, "rev": b_idx, "orig_idx": e["orig_idx"]}
            b_edge = {"u": v, "v": u, "cap": 0.0, "flow": 0.0, "rev": f_idx, "orig_idx": e["orig_idx"]}
            raw_list.extend([f_edge, b_edge])

        self.raw_edges = raw_list
        self.graph = [[] for _ in range(self.n)]
        for i, e in enumerate(self.raw_edges):
            self.graph[e["u"]].append(i)

        max_flow = 0.0
        INF = float("inf")

        while self._bfs(s, t):
            self.ptr = [0] * self.n
            while True:
                pushed = self._dfs(s, t, INF)
                if pushed <= 1e-9:
                    break
                max_flow += pushed

        edge_flows = [0.0] * len(self.edges)
        for e in self.raw_edges[::2]:  # Original forward edges only
            edge_flows[e["orig_idx"]] = e["flow"]

        return max_flow, edge_flows


# --- Example Usage ---
if __name__ == "__main__":
    # Define a graph with 4 nodes (0, 1, 2, 3)
    dinic = DinicMaxFlow(num_nodes=4)

    # Add directed edges: (u, v, capacity)
    e0 = dinic.add_edge(0, 1, 10.0)
    e1 = dinic.add_edge(0, 2, 10.0)
    e2 = dinic.add_edge(1, 2, 2.0)
    e3 = dinic.add_edge(1, 3, 4.0)
    e4 = dinic.add_edge(2, 3, 8.0)

    source, sink = 0, 3
    max_flow, flows = dinic.solve(source, sink)

    print(f"Maximum s-t Flow: {max_flow}")
    print("Flow on each original edge (in input order):")
    for idx, flow in enumerate(flows):
        orig = dinic.edges[idx]
        print(f"Edge {idx} ({orig['u']} -> {orig['v']}): {flow} / {orig['cap']}")