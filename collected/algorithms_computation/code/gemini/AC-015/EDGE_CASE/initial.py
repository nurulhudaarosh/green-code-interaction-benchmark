from collections import deque

class DinicMaxFlow:
    """
    Computes maximum s-t flow using Dinic's Algorithm.
    Preserves the original order of edges in the output.
    """

    def __init__(self, num_nodes: int):
        self.num_nodes = num_nodes
        self.graph = [[] for _ in range(num_nodes)]
        self.edges = []
        self.original_edge_indices = []

    def add_edge(self, u: int, v: int, capacity: float):
        """
        Adds a directed edge from u to v with given capacity.
        Returns the index corresponding to this original edge.
        """
        forward_idx = len(self.edges)
        # Forward edge
        self.edges.append({'u': u, 'v': v, 'cap': capacity, 'flow': 0.0})
        self.graph[u].append(forward_idx)

        # Backward edge (reverse capacity initialized to 0)
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
                if residual > 1e-9 and level[edge['v']] == -1:
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
            if residual <= 1e-9:
                continue

            tr = self._dfs(v, t, min(pushed, residual), level, ptr)
            if tr <= 1e-9:
                continue

            # Update forward and residual flows
            self.edges[edge_idx]['flow'] += tr
            self.edges[edge_idx ^ 1]['flow'] -= tr
            return tr

        return 0.0

    def compute_max_flow(self, s: int, t: int):
        """
        Calculates maximum flow from s to t.
        Returns a tuple: (max_flow_val, list_of_edge_flows)
        """
        max_flow_val = 0.0
        level = [-1] * self.num_nodes

        while self._bfs(s, t, level):
            ptr = [0] * self.num_nodes
            while True:
                pushed = self._dfs(s, t, float('inf'), level, ptr)
                if pushed <= 1e-9:
                    break
                max_flow_val += pushed

        edge_flows = [self.edges[idx]['flow'] for idx in self.original_edge_indices]
        return max_flow_val, edge_flows


# --- Example Usage ---
if __name__ == "__main__":
    # Graph layout:
    # 0 -> 1 (cap 10), 0 -> 2 (cap 10)
    # 1 -> 2 (cap 2),  1 -> 3 (cap 4), 1 -> 4 (cap 8)
    # 2 -> 4 (cap 9)
    # 3 -> 5 (cap 10)
    # 4 -> 3 (cap 6),  4 -> 5 (cap 10)

    n_nodes = 6
    source, sink = 0, 5

    input_edges = [
        (0, 1, 10.0),
        (0, 2, 10.0),
        (1, 2, 2.0),
        (1, 3, 4.0),
        (1, 4, 8.0),
        (2, 4, 9.0),
        (3, 5, 10.0),
        (4, 3, 6.0),
        (4, 5, 10.0),
    ]

    dinic = DinicMaxFlow(n_nodes)
    for u, v, cap in input_edges:
        dinic.add_edge(u, v, cap)

    max_flow, edge_flows = dinic.compute_max_flow(source, sink)

    print(f"Maximum Flow: {max_flow:.2f}\n")
    print("Edge Flow Details (Preserving Original Input Order):")
    for i, (u, v, cap) in enumerate(input_edges):
        print(f"Edge {i} ({u} -> {v}): Flow = {edge_flows[i]:.2f} / Capacity = {cap:.2f}")