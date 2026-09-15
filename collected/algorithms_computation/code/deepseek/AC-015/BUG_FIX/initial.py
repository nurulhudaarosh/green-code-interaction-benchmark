import sys
from collections import deque

class Dinic:
    def __init__(self, n):
        self.n = n
        self.graph = [[] for _ in range(n)]
        self.edges = []  # Store original edges for output
        self.edge_map = []  # Maps original edge index to (u, edge_index_in_graph)
    
    def add_edge(self, u, v, cap):
        """Add directed edge u->v with capacity cap."""
        # Forward edge
        forward = [v, cap, len(self.graph[v])]
        # Backward edge
        backward = [u, 0, len(self.graph[u])]
        
        self.graph[u].append(forward)
        self.graph[v].append(backward)
        
        # Store original edge info
        self.edges.append((u, v, cap))
        self.edge_map.append((u, len(self.graph[u]) - 1))
    
    def bfs(self, s, t):
        """Build level graph using BFS. Returns True if t is reachable."""
        self.level = [-1] * self.n
        self.level[s] = 0
        queue = deque([s])
        
        while queue:
            u = queue.popleft()
            for edge in self.graph[u]:
                v, cap, _ = edge
                if cap > 0 and self.level[v] == -1:
                    self.level[v] = self.level[u] + 1
                    queue.append(v)
        
        return self.level[t] != -1
    
    def dfs(self, u, t, pushed):
        """Find blocking flow using DFS with level graph."""
        if u == t:
            return pushed
        
        while self.it[u] < len(self.graph[u]):
            edge = self.graph[u][self.it[u]]
            v, cap, rev = edge
            
            if cap > 0 and self.level[v] == self.level[u] + 1:
                flow = self.dfs(v, t, min(pushed, cap))
                if flow > 0:
                    # Update forward edge
                    self.graph[u][self.it[u]][1] -= flow
                    # Update backward edge
                    self.graph[v][rev][1] += flow
                    return flow
            
            self.it[u] += 1
        
        return 0
    
    def max_flow(self, s, t):
        """Compute maximum flow from s to t."""
        flow = 0
        
        while self.bfs(s, t):
            self.it = [0] * self.n
            
            while True:
                pushed = self.dfs(s, t, float('inf'))
                if pushed == 0:
                    break
                flow += pushed
        
        return flow
    
    def get_edge_flows(self):
        """Get flow on each original edge in original order."""
        flows = []
        for u, edge_idx in self.edge_map:
            # Flow = original capacity - remaining capacity
            original_cap = self.edges[len(flows)][2]
            remaining_cap = self.graph[u][edge_idx][1]
            flows.append(original_cap - remaining_cap)
        return flows


def solve_max_flow(n, m, s, t, edges):
    """
    Solve maximum flow problem.
    
    Args:
        n: number of nodes (0-indexed)
        m: number of edges
        s: source node
        t: sink node
        edges: list of (u, v, capacity) tuples
    
    Returns:
        (max_flow_value, list_of_edge_flows)
    """
    dinic = Dinic(n)
    
    for u, v, cap in edges:
        dinic.add_edge(u, v, cap)
    
    max_flow_value = dinic.max_flow(s, t)
    edge_flows = dinic.get_edge_flows()
    
    return max_flow_value, edge_flows


def main():
    """Main function to read input and produce output."""
    # Read all input
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    idx = 0
    n = int(data[idx]); idx += 1
    m = int(data[idx]); idx += 1
    s = int(data[idx]); idx += 1
    t = int(data[idx]); idx += 1
    
    edges = []
    for _ in range(m):
        u = int(data[idx]); idx += 1
        v = int(data[idx]); idx += 1
        cap = int(data[idx]); idx += 1
        edges.append((u, v, cap))
    
    max_flow_value, edge_flows = solve_max_flow(n, m, s, t, edges)
    
    # Output
    print(max_flow_value)
    for flow in edge_flows:
        print(flow)


if __name__ == "__main__":
    main()