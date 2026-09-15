from collections import deque
import math
import sys

class DinicMaxFlowPlanner:
    """
    Computes maximum s-t flow using Dinic's Algorithm.
    Fully handles boundary conditions, floating-point precision, multi-edges,
    and preserves original edge insertion order in output.
    """

    def __init__(self, num_nodes: int):
        if num_nodes < 0:
            raise ValueError("Number of nodes must be non-negative.")
        self.num_nodes = num_nodes
        self.graph = [[] for _ in range(num_nodes)]
        self.edges = []
        self.original_edge_indices = []

    def add_edge(self, u: int, v: int, capacity: float) -> int:
        """
        Adds a directed edge from u to v with specified capacity.
        Returns the original edge index.
        """
        if not (0 <= u < self.num_nodes and 0 <= v < self.num_nodes):
            raise IndexError(f"Node indices ({u}, {v}) out of range [0, {self.num_nodes-1}]")
        if capacity < 0:
            raise ValueError(f"Capacity must be non-negative, got {capacity}")

        forward_idx = len(self.edges)
        
        # Forward edge
        self.edges.append({'u': u, 'v': v, 'cap': float(capacity), 'flow': 0.0})
        self.graph[u].append(forward_idx)

        # Reverse residual edge (capacity 0.0)
        backward_idx = len(self.edges)
        self.edges.append({'u': v, 'v': u, 'cap': 0.0, 'flow': 0.0})
        self.graph[v].append(backward_idx)

        self.original_edge_indices.append(forward_idx)
        return len(self.original_edge_indices) - 1

    def _bfs(self, s: int, t: int, level: list) -> bool:
        for i in range(self.num_nodes):
            level[i] = -1
        level[s] = 0

        queue = deque([s])
        while queue:
            u = queue.popleft()
            for edge_idx in self.graph[u]:
                edge = self.edges[edge_idx]
                residual = edge['cap'] - edge['flow']
                if residual > 1e-12 and level[edge['v']] == -1:
                    level[edge['v']] = level[u] + 1
                    queue.append(edge['v'])

        return level[t] != -1

    def _dfs(self, u: int, t: int, pushed: float, level: list, ptr: list) -> float:
        if pushed <= 0 or u == t:
            return pushed

        for i in range(ptr[u], len(self.graph[u])):
            ptr[u] = i
            edge_idx = self.graph[u][i]
            edge = self.edges[edge_idx]
            v = edge['v']

            if level[u] + 1 != level[v]:
                continue

            residual = edge['cap'] - edge['flow']
            if residual <= 1e-12:
                continue

            tr = self._dfs(v, t, min(pushed, residual), level, ptr)
            if tr <= 1e-12:
                continue

            self.edges[edge_idx]['flow'] += tr
            self.edges[edge_idx ^ 1]['flow'] -= tr
            return tr

        return 0.0

    def compute_max_flow(self, s: int, t: int):
        """
        Computes maximum flow from source s to sink t.
        Returns tuple: (total_max_flow, list_of_flows_per_original_edge)
        """
        # Boundary case: s or t out of bounds
        if not (0 <= s < self.num_nodes and 0 <= t < self.num_nodes):
            raise IndexError("Source or Sink node index out of bounds.")

        # Boundary case: Source equals Sink or zero-node graph
        if s == t or self.num_nodes == 0:
            edge_flows = [0.0] * len(self.original_edge_indices)
            return 0.0, edge_flows

        max_flow_val = 0.0
        level = [-1] * self.num_nodes

        while self._bfs(s, t, level):
            ptr = [0] * self.num_nodes
            while True:
                pushed = self._dfs(s, t, float('inf'), level, ptr)
                if pushed <= 1e-12:
                    break
                max_flow_val += pushed

        edge_flows = [self.edges[idx]['flow'] for idx in self.original_edge_indices]
        return max_flow_val, edge_flows


# --- Comprehensive Unit Test Suite ---

def run_boundary_tests():
    print("Running Dinic Max Flow Boundary Tests...")

    # Test 1: Disconnected Source and Sink
    planner = DinicMaxFlowPlanner(4)
    planner.add_edge(0, 1, 10.0)
    planner.add_edge(2, 3, 5.0)
    flow, edge_flows = planner.compute_max_flow(0, 3)
    assert math.isclose(flow, 0.0), f"Test 1 Failed: Expected 0.0, got {flow}"
    assert edge_flows == [0.0, 0.0], f"Test 1 Edge Flow Failed: {edge_flows}"
    print("✓ Test 1 Passed: Disconnected Graph")

    # Test 2: Source equals Sink (s == t)
    planner = DinicMaxFlowPlanner(3)
    planner.add_edge(0, 1, 10.0)
    planner.add_edge(1, 2, 5.0)
    flow, edge_flows = planner.compute_max_flow(1, 1)
    assert math.isclose(flow, 0.0), f"Test 2 Failed: Expected 0.0, got {flow}"
    assert edge_flows == [0.0, 0.0], f"Test 2 Edge Flow Failed: {edge_flows}"
    print("✓ Test 2 Passed: Source Equals Sink")

    # Test 3: Zero-Capacity Edges & Self-Loops
    planner = DinicMaxFlowPlanner(3)
    planner.add_edge(0, 0, 100.0)  # Self-loop
    planner.add_edge(0, 1, 0.0)    # Zero capacity
    planner.add_edge(1, 2, 10.0)   # Normal edge
    flow, edge_flows = planner.compute_max_flow(0, 2)
    assert math.isclose(flow, 0.0), f"Test 3 Failed: Expected 0.0, got {flow}"
    assert edge_flows == [0.0, 0.0, 0.0], f"Test 3 Edge Flow Failed: {edge_flows}"
    print("✓ Test 3 Passed: Self-Loops & Zero-Capacity Edges")

    # Test 4: Parallel Edges (Multi-edges) preserving original order
    planner = DinicMaxFlowPlanner(3)
    idx0 = planner.add_edge(0, 1, 5.0)
    idx1 = planner.add_edge(0, 1, 15.0)
    idx2 = planner.add_edge(1, 2, 12.0)
    flow, edge_flows = planner.compute_max_flow(0, 2)
    assert math.isclose(flow, 12.0), f"Test 4 Failed: Expected 12.0, got {flow}"
    assert math.isclose(edge_flows[idx0], 5.0), f"Edge 0 flow expected 5.0, got {edge_flows[idx0]}"
    assert math.isclose(edge_flows[idx1], 7.0), f"Edge 1 flow expected 7.0, got {edge_flows[idx1]}"
    assert math.isclose(edge_flows[idx2], 12.0), f"Edge 2 flow expected 12.0, got {edge_flows[idx2]}"
    print("✓ Test 4 Passed: Parallel Edges & Output Order Preservation")

    # Test 5: Fractional Capacities & Small Epsilon Handling
    planner = DinicMaxFlowPlanner(3)
    planner.add_edge(0, 1, 0.000000001)
    planner.add_edge(1, 2, 0.000000001)
    flow, edge_flows = planner.compute_max_flow(0, 2)
    assert math.isclose(flow, 1e-9, rel_tol=1e-7), f"Test 5 Failed: Expected 1e-9, got {flow}"
    print("✓ Test 5 Passed: Fractional Capacities")

    # Test 6: Single-Node Graph / Empty Graph Limits
    planner = DinicMaxFlowPlanner(1)
    flow, edge_flows = planner.compute_max_flow(0, 0)
    assert math.isclose(flow, 0.0) and edge_flows == [], "Test 6 Failed: Single node"
    print("✓ Test 6 Passed: Single-Node Graph")

    print("\nAll boundary and deterministic edge case tests passed successfully!")

if __name__ == "__main__":
    run_boundary_tests()