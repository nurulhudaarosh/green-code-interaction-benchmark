class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_component_size = 1 if n > 0 else 0

    def find(self, i: int) -> int:
        path = []
        while self.parent[i] != i:
            path.append(i)
            i = self.parent[i]
        for node in path:
            self.parent[node] = i
        return i

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)
        
        if root_i != root_j:
            # Union by size
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            
            if self.size[root_i] > self.max_component_size:
                self.max_component_size = self.size[root_i]
                
            self.num_components -= 1
            return True
        return False


def solve_threshold_queries(
    n: int, 
    edges: list[tuple[int, int, int]], 
    queries: list[int]
) -> list[tuple[int, int]]:
    """
    n: Number of vertices (0 to n-1)
    edges: List of tuples (u, v, weight)
    queries: List of weight thresholds q
    
    Returns:
        List of tuples (num_components, max_component_size) for each query in original order.
    """
    # Sort edges by weight
    sorted_edges = sorted(edges, key=lambda x: x[2])
    
    # Sort queries while preserving original indices: (threshold, original_index)
    indexed_queries = sorted(enumerate(queries), key=lambda x: x[1])
    
    dsu = UnionFind(n)
    results = [(0, 0)] * len(queries)
    
    edge_idx = 0
    num_edges = len(sorted_edges)
    
    for orig_idx, q in indexed_queries:
        # Add all edges with weight <= q
        while edge_idx < num_edges and sorted_edges[edge_idx][2] <= q:
            u, v, _ = sorted_edges[edge_idx]
            dsu.union(u, v)
            edge_idx += 1
            
        results[orig_idx] = (dsu.num_components, dsu.max_component_size)
        
    return results


# Example Usage:
if __name__ == "__main__":
    n = 5
    # (u, v, weight)
    edges = [
        (0, 1, 2),
        (1, 2, 5),
        (2, 3, 3),
        (3, 4, 8)
    ]
    queries = [1, 3, 5, 10]
    
    output = solve_threshold_queries(n, edges, queries)
    for q, res in zip(queries, output):
        print(f"Query q={q}: Components = {res[0]}, Max Size = {res[1]}")