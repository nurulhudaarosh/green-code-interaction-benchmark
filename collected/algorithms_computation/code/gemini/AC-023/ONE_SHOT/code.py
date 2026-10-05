class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_size = 1 if n > 0 else 0

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> None:
        root_i = self.find(i)
        root_j = self.find(j)
        
        if root_i != root_j:
            # Union by size
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            
            self.num_components -= 1
            if self.size[root_i] > self.max_size:
                self.max_size = self.size[root_i]


def component_stats_per_threshold(n: int, edges: list[tuple[int, int, int]], queries: list[int]) -> list[tuple[int, int]]:
    """
    n: number of vertices (0 to n-1)
    edges: list of tuples (u, v, weight)
    queries: list of weight thresholds Q

    Returns:
    List of tuples (num_components, max_component_size) for each query in original order.
    """
    # Sort edges by weight
    sorted_edges = sorted(edges, key=lambda e: e[2])
    
    # Sort queries keeping track of original indices
    indexed_queries = sorted(enumerate(queries), key=lambda x: x[1])
    
    uf = UnionFind(n)
    ans = [(0, 0)] * len(queries)
    
    edge_idx = 0
    num_edges = len(sorted_edges)
    
    for original_idx, q_val in indexed_queries:
        # Add all edges with weight <= threshold q_val
        while edge_idx < num_edges and sorted_edges[edge_idx][2] <= q_val:
            u, v, w = sorted_edges[edge_idx]
            uf.union(u, v)
            edge_idx += 1
            
        ans[original_idx] = (uf.num_components, uf.max_size)
        
    return ans