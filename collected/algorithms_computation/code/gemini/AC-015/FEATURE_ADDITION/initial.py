from collections import deque
from typing import List, Tuple

class DinicMaxFlow:
    def __init__(self, num_nodes: int):
        self.n = num_nodes
        self.graph = [[] for _ in range(num_nodes)]
        self.edges = []  # Stores (u, v, capacity, flow)
        self.level = []
        self.ptr = []

    def add_edge(self, u: int, v: int, cap: int) -> int:
        """Adds a directed edge (u, v) with capacity cap. Returns original edge index."""
        forward_edge_idx = len(self.edges)
        # Forward edge
        self.edges.append({'u': u, 'v': v, 'cap': cap, 'flow': 0, 'rev': forward_edge_idx + 1})
        self.graph[u].append(forward_edge_idx)
        
        # Reverse edge (capacity 0)
        self.edges.append({'u': v, 'v': u, 'cap': 0, 'flow': 0, 'rev': forward_edge_idx})
        self.graph[v].append(forward_edge_idx + 1)
        
        return forward_edge_idx

    def _bfs(self, s: int, t: int) -> bool:
        """Builds the level graph using BFS."""
        self.level = [-1] * self.n
        self.level[s] = 0
        queue = deque([s])
        
        while queue:
            u = queue.popleft()
            for edge_idx in self.graph[u]:
                edge = self.edges[edge_idx]
                if edge['cap'] - edge['flow'] > 0 and self.level[edge['v']] == -1:
                    self.level[edge['v']] = self.level[u] + 1
                    queue.append(edge['v'])
                    
        return self.level[t] != -1

    def _dfs(self, u: int, t: int, pushed: int) -> int:
        """Pushes blocking flow through level graph using DFS."""
        if pushed == 0 or u == t:
            return pushed
        
        for i in range(self.ptr[u], len(self.graph[u])):
            edge_idx = self.graph[u][i]
            edge = self.edges[edge_idx]
            v = edge['v']
            
            if self.level[u] + 1 != self.level[v] or edge['cap'] - edge['flow'] == 0:
                self.ptr[u] += 1
                continue
            
            tr = self._dfs(v, t, min(pushed, edge['cap'] - edge['flow']))
            if tr == 0:
                self.ptr[u] += 1
                continue
            
            # Update forward and reverse residual flows
            self.edges[edge_idx]['flow'] += tr
            self.edges[edge_idx ^ 1]['flow'] -= tr
            return tr
            
        return 0

    def max_flow(self, s: int, t: int) -> Tuple[int, List[int]]:
        """Computes max flow and returns (max_flow_value, list_of_edge_flows)."""
        flow_value = 0
        INF = float('inf')
        
        while self._bfs(s, t):
            self.ptr = [0] * self.n
            while True:
                pushed = self._dfs(s, t, INF)
                if pushed == 0:
                    break
                flow_value += pushed
                
        # Extract flow for original input edges (every even-indexed internal edge)
        edge_flows = [self.edges[i]['flow'] for i in range(0, len(self.edges), 2)]
        return flow_value, edge_flows


# Example Usage & Verification:
if __name__ == "__main__":
    # Define network topology: 4 nodes (0=s, 3=t), 5 edges
    num_nodes = 4
    source, sink = 0, 3
    
    input_edges = [
        (0, 1, 10), # Edge 0
        (0, 2, 10), # Edge 1
        (1, 2, 2),  # Edge 2
        (1, 3, 4),  # Edge 3
        (2, 3, 10)  # Edge 4
    ]
    
    dinic = DinicMaxFlow(num_nodes)
    for u, v, cap in input_edges:
        dinic.add_edge(u, v, cap)
        
    total_flow, original_edge_flows = dinic.max_flow(source, sink)
    
    print(f"Maximum Flow: {total_flow}")
    print("\nFlow per Edge (in original order):")
    for i, (u, v, cap) in enumerate(input_edges):
        print(f"Edge {i} ({u} -> {v}, Cap: {cap}): Flow = {original_edge_flows[i]}")