from collections import deque
from typing import Dict, List, Tuple, Union


class DinicMaxFlow:
    """Computes Maximum s-t Flow using Dinic's blocking-flow algorithm.

    Handles boundary input limits, deterministic tie-breaking, and optional
    operation summaries.
    """

    def __init__(self, num_nodes: int):
        self.n = num_nodes
        self.graph = [[] for _ in range(num_nodes)]
        self.raw_edges = []
        self.num_original_edges = 0

    def add_edge(self, u: int, v: int, capacity: float) -> int:
        """Adds a directed edge from u to v with specified capacity.

        Returns 0-based insertion index.
        """
        if u < 0 or u >= self.n or v < 0 or v >= self.n:
            raise ValueError(
                f"Node indices ({u}, {v}) out of valid range [0, {self.n - 1}]."
            )

        orig_idx = self.num_original_edges
        self.num_original_edges += 1

        fwd_id = len(self.raw_edges)
        rev_id = fwd_id + 1

        forward_edge = {
            "u": u,
            "v": v,
            "cap": float(capacity),
            "flow": 0.0,
            "rev": rev_id,
            "orig_idx": orig_idx,
            "is_original": True,
        }
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
        """Constructs level graph via deterministic BFS."""
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

    def _dfs(
        self, u: int, t: int, pushed: float, metrics: Dict[str, int]
    ) -> float:
        """Pushes blocking flow through level graph via DFS."""
        if pushed <= 0:
            return 0.0
        if u == t:
            metrics["dfs_augmentations"] += 1
            return pushed

        while self.ptr[u] < len(self.graph[u]):
            cid = self.ptr[u]
            edge_id = self.graph[u][cid]
            edge = self.raw_edges[edge_id]
            v = edge["v"]
            residual_cap = edge["cap"] - edge["flow"]

            metrics["dfs_steps"] += 1

            if self.level[u] + 1 == self.level[v] and residual_cap > 1e-9:
                tr = self._dfs(v, t, min(pushed, residual_cap), metrics)
                if tr > 1e-9:
                    edge["flow"] += tr
                    self.raw_edges[edge["rev"]]["flow"] -= tr
                    return tr

            self.ptr[u] += 1

        return 0.0

    def solve(
        self, s: int, t: int, return_summary: bool = False
    ) -> Union[Tuple[float, List[float]], Tuple[float, List[float], Dict]]:
        """Solves the maximum flow problem from s to t."""
        if s < 0 or s >= self.n or t < 0 or t >= self.n:
            raise ValueError(
                f"Source ({s}) or Sink ({t}) node out of range [0, {self.n - 1}]."
            )

        # Reset flows across all edges
        for edge in self.raw_edges:
            edge["flow"] = 0.0

        metrics = {"bfs_phases": 0, "dfs_augmentations": 0, "dfs_steps": 0}

        # Boundary condition: Source equals sink
        if s == t:
            edge_flows = [0.0] * self.num_original_edges
            if not return_summary:
                return 0.0, edge_flows
            return 0.0, edge_flows, {**metrics, "max_flow": 0.0, "edge_flows": edge_flows}

        max_flow = 0.0
        INF = float("inf")

        while self._bfs(s, t):
            metrics["bfs_phases"] += 1
            self.ptr = [0] * self.n
            while True:
                pushed = self._dfs(s, t, INF, metrics)
                if pushed <= 1e-9:
                    break
                max_flow += pushed

        edge_flows = [0.0] * self.num_original_edges
        for edge_id in range(0, len(self.raw_edges), 2):
            edge = self.raw_edges[edge_id]
            edge_flows[edge["orig_idx"]] = max(0.0, edge["flow"])

        if not return_summary:
            return max_flow, edge_flows

        operation_summary = {
            "bfs_phases": metrics["bfs_phases"],
            "dfs_augmentations": metrics["dfs_augmentations"],
            "dfs_steps": metrics["dfs_steps"],
            "max_flow": max_flow,
            "edge_flows": edge_flows,
        }

        return max_flow, edge_flows, operation_summary


# --- Boundary Test Suite ---
def run_boundary_tests():
    print("Executing Boundary Value Unit Tests...\n")

    # Test 1: Source == Sink
    g1 = DinicMaxFlow(num_nodes=3)
    g1.add_edge(0, 1, 10.0)
    g1.add_edge(1, 2, 5.0)
    mf, flows = g1.solve(s=1, t=1)
    assert mf == 0.0 and flows == [0.0, 0.0], "Test 1 Failed: Source == Sink"
    print("[PASS] Test 1: Source == Sink returns 0.0 flow.")

    # Test 2: Unreachable / Disconnected Sink
    g2 = DinicMaxFlow(num_nodes=4)
    g2.add_edge(0, 1, 10.0)
    g2.add_edge(2, 3, 10.0)
    mf, flows = g2.solve(s=0, t=3)
    assert mf == 0.0 and flows == [0.0, 0.0], "Test 2 Failed: Disconnected Sink"
    print("[PASS] Test 2: Disconnected graph returns 0.0 flow.")

    # Test 3: Zero-capacity Edges
    g3 = DinicMaxFlow(num_nodes=3)
    g3.add_edge(0, 1, 0.0)
    g3.add_edge(1, 2, 10.0)
    mf, flows = g3.solve(s=0, t=2)
    assert mf == 0.0 and flows == [0.0, 0.0], "Test 3 Failed: Zero capacity edge"
    print("[PASS] Test 3: Zero-capacity edge handled correctly.")

    # Test 4: Graph with no edges
    g4 = DinicMaxFlow(num_nodes=2)
    mf, flows = g4.solve(s=0, t=1)
    assert mf == 0.0 and flows == [], "Test 4 Failed: No edges graph"
    print("[PASS] Test 4: Empty edge graph handled correctly.")

    # Test 5: Parallel / Multi-edges preserve original order
    g5 = DinicMaxFlow(num_nodes=2)
    e0 = g5.add_edge(0, 1, 3.0)  # First parallel edge
    e1 = g5.add_edge(0, 1, 7.0)  # Second parallel edge
    mf, flows = g5.solve(s=0, t=1)
    assert mf == 10.0 and flows == [3.0, 7.0], "Test 5 Failed: Multi-edges"
    print("[PASS] Test 5: Parallel edges push flow deterministically in order.")

    # Test 6: Self-loop handling
    g6 = DinicMaxFlow(num_nodes=3)
    g6.add_edge(0, 0, 100.0)  # Self-loop on source
    g6.add_edge(0, 1, 5.0)
    g6.add_edge(1, 2, 5.0)
    mf, flows = g6.solve(s=0, t=2)
    assert mf == 5.0 and flows == [0.0, 5.0, 5.0], "Test 6 Failed: Self loop"
    print("[PASS] Test 6: Self-loop edge safely ignored.")

    print("\nAll boundary test cases passed successfully.")


if __name__ == "__main__":
    run_boundary_tests()