from collections import deque
from typing import List, Tuple


class DinicMaxFlow:
    """Computes Maximum s-t Flow using Dinic's blocking-flow algorithm with

    deterministic tie-handling and original edge order preservation.
    """

    def __init__(self, num_nodes: int):
        self.n = num_nodes
        self.graph = [[] for _ in range(num_nodes)]
        self.raw_edges = []
        self.num_original_edges = 0

    def add_edge(self, u: int, v: int, capacity: float) -> int:
        """Adds a directed edge from u to v with specified capacity.

        Returns the 0-based index of the original edge.
        """
        orig_idx = self.num_original_edges
        self.num_original_edges += 1

        fwd_id = len(self.raw_edges)
        rev_id = fwd_id + 1

        # Forward residual edge
        forward_edge = {
            "u": u,
            "v": v,
            "cap": float(capacity),
            "flow": 0.0,
            "rev": rev_id,
            "orig_idx": orig_idx,
            "is_original": True,
        }
        # Backward residual edge
        backward_edge = {
            "u": v,
            "v": u,
            "cap": 0.0,
            "flow": 0.0,
            "rev": fwd_id,
            "orig_idx": orig_idx,
            "is_original": False,
        }

        self.raw_edges.append(forward_edge)
        self.raw_edges.append(backward_edge)

        self.graph[u].append(fwd_id)
        self.graph[v].append(rev_id)

        return orig_idx

    def _bfs(self, s: int, t: int) -> bool:
        """Constructs the level graph via BFS."""
        self.level = [-1] * self.n
        self.level[s] = 0
        queue = deque([s])

        while queue:
            u = queue.popleft()
            for edge_id in self.graph[u]:
                edge = self.raw_edges[edge_id]
                residual_cap = edge["cap"] - edge["flow"]
                if residual_cap > 1e-9 and self.level[edge["v"]] == -1:
                    self.level[edge["v"]] = self.level[u] + 1
                    queue.append(edge["v"])

        return self.level[t] != -1

    def _dfs(self, u: int, t: int, pushed: float) -> float:
        """Pushes blocking flow through the level graph via DFS."""
        if pushed <= 0:
            return 0.0
        if u == t:
            return pushed

        while self.ptr[u] < len(self.graph[u]):
            cid = self.ptr[u]
            edge_id = self.graph[u][cid]
            edge = self.raw_edges[edge_id]
            v = edge["v"]
            residual_cap = edge["cap"] - edge["flow"]

            if self.level[u] + 1 == self.level[v] and residual_cap > 1e-9:
                tr = self._dfs(v, t, min(pushed, residual_cap))
                if tr > 1e-9:
                    edge["flow"] += tr
                    self.raw_edges[edge["rev"]]["flow"] -= tr
                    return tr

            # Edge is saturated or cannot reach sink in current level graph
            self.ptr[u] += 1

        return 0.0

    def solve(self, s: int, t: int) -> Tuple[float, List[float]]:
        """Computes the maximum s-t flow.

        Returns:
            (max_flow, edge_flows):
                - max_flow: Total maximum flow value from s to t.
                - edge_flows: List of flows assigned to original edges in input
                order.
        """
        # Reset flow on all edges for clean execution
        for edge in self.raw_edges:
            edge["flow"] = 0.0

        max_flow = 0.0
        INF = float("inf")

        while self._bfs(s, t):
            self.ptr = [0] * self.n
            while True:
                pushed = self._dfs(s, t, INF)
                if pushed <= 1e-9:
                    break
                max_flow += pushed

        # Extract flows for original edges in exact insertion order
        edge_flows = [0.0] * self.num_original_edges
        for edge_id in range(0, len(self.raw_edges), 2):
            edge = self.raw_edges[edge_id]
            edge_flows[edge["orig_idx"]] = max(0.0, edge["flow"])

        return max_flow, edge_flows


# --- Verification ---
if __name__ == "__main__":
    solver = DinicMaxFlow(num_nodes=4)

    # Input edge order preserved explicitly
    e0 = solver.add_edge(0, 1, 10.0)
    e1 = solver.add_edge(0, 2, 10.0)
    e2 = solver.add_edge(1, 2, 2.0)
    e3 = solver.add_edge(1, 3, 4.0)
    e4 = solver.add_edge(2, 3, 8.0)

    max_flow, flows = solver.solve(s=0, t=3)

    assert max_flow == 12.0
    assert flows == [4.0, 8.0, 0.0, 4.0, 8.0]

    print(f"Computed Max Flow: {max_flow}")
    print(f"Edge Flows (Input Order): {flows}")