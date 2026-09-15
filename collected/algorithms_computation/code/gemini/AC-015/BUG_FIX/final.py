from collections import deque
from typing import List, Tuple


class ResidualEdge:
    def __init__(self, to: int, rev_idx: int, capacity: int, original_edge_id: int):
        self.to = to
        self.rev_idx = rev_idx
        self.cap = capacity
        self.flow = 0
        self.original_edge_id = original_edge_id


class MaximumFlowPlanner:
    def __init__(self, num_nodes: int):
        self.n = num_nodes
        self.adj: List[List[ResidualEdge]] = [[] for _ in range(num_nodes)]
        self.level: List[int] = [-1] * num_nodes
        self.ptr: List[int] = [0] * num_nodes
        # Directly store pointers to forward edges by original input index
        self.original_edges: List[ResidualEdge] = []

    def add_edge(self, u: int, v: int, capacity: int) -> None:
        """
        Adds a directed edge from u to v.
        Deterministic tie handling is preserved by processing edges 
        in insertion order during BFS and DFS traversals.
        """
        original_id = len(self.original_edges)
        
        # Forward edge
        u_to_v = ResidualEdge(
            to=v, 
            rev_idx=len(self.adj[v]), 
            capacity=capacity, 
            original_edge_id=original_id
        )
        # Residual backward edge (capacity 0, non-original)
        v_to_u = ResidualEdge(
            to=u, 
            rev_idx=len(self.adj[u]), 
            capacity=0, 
            original_edge_id=-1
        )

        self.adj[u].append(u_to_v)
        self.adj[v].append(v_to_u)
        
        # Track the forward edge reference directly
        self.original_edges.append(u_to_v)

    def _bfs(self, s: int, t: int) -> bool:
        """Constructs the level graph using standard BFS (deterministic queue ordering)."""
        self.level = [-1] * self.n
        self.level[s] = 0
        queue = deque([s])

        while queue:
            u = queue.popleft()
            for edge in self.adj[u]:
                if edge.cap - edge.flow > 0 and self.level[edge.to] < 0:
                    self.level[edge.to] = self.level[u] + 1
                    queue.append(edge.to)

        return self.level[t] >= 0

    def _dfs(self, u: int, t: int, pushed: int) -> int:
        """Pushes flow through the level graph using DFS with current-edge pointers."""
        if pushed == 0 or u == t:
            return pushed

        for cid in range(self.ptr[u], len(self.adj[u])):
            self.ptr[u] = cid
            edge = self.adj[u][cid]
            tr = edge.to

            # Strict level graph progression check
            if self.level[u] + 1 != self.level[tr] or edge.cap - edge.flow == 0:
                continue

            tr_pushed = self._dfs(tr, t, min(pushed, edge.cap - edge.flow))
            if tr_pushed == 0:
                continue

            # Update residual flows symmetrically
            edge.flow += tr_pushed
            self.adj[tr][edge.rev_idx].flow -= tr_pushed
            return tr_pushed

        return 0

    def solve(self, s: int, t: int) -> Tuple[int, List[int]]:
        """
        Computes maximum flow using Dinic's Algorithm.
        Returns:
            - max_flow (int): The total maximum flow from s to t.
            - edge_flows (List[int]): Flow on each original edge in exact input order.
        """
        max_flow = 0

        # Dinic's main loop
        while self._bfs(s, t):
            self.ptr = [0] * self.n
            while True:
                pushed = self._dfs(s, t, float('inf'))
                if pushed == 0:
                    break
                max_flow += pushed

        # Extract flows directly using stored original edge references
        edge_flows = [edge.flow for edge in self.original_edges]

        return max_flow, edge_flows


# --- Verification with Parallel Edges ---
if __name__ == "__main__":
    planner = MaximumFlowPlanner(num_nodes=2)
    
    # Adding two parallel edges from Node 0 -> Node 1
    input_edges = [
        (0, 1, 5),   # Edge 0
        (0, 1, 10),  # Edge 1
    ]

    for u, v, cap in input_edges:
        planner.add_edge(u, v, cap)

    max_flow, flows = planner.solve(s=0, t=1)

    print(f"Max Flow Computed: {max_flow}")
    print(f"Per-Edge Flows (Preserving Order): {flows}")
    assert max_flow == 15
    assert flows == [5, 10]
    print("\nDefect test passed successfully!")