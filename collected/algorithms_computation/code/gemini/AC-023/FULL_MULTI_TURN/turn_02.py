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
            # Deterministic union by size; tie-break by smaller root index for strict determinism
            if self.size[root_i] < self.size[root_j] or (
                self.size[root_i] == self.size[root_j] and root_i > root_j
            ):
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
    # Canonicalize and deterministically sort edges by (weight, min(u, v), max(u, v))
    sorted_edges = sorted(
        [(w, min(u, v), max(u, v)) for u, v, w in edges],
        key=lambda x: (x[0], x[1], x[2])
    )
    
    # Deterministically sort queries by (threshold, original_index)
    indexed_queries = sorted(
        enumerate(queries), 
        key=lambda x: (x[1], x[0])
    )
    
    dsu = UnionFind(n)
    results = [(0, 0)] * len(queries)
    
    edge_idx = 0
    num_edges = len(sorted_edges)
    
    for orig_idx, q in indexed_queries:
        # Add all edges with weight <= q in deterministic order
        while edge_idx < num_edges and sorted_edges[edge_idx][0] <= q:
            _, u, v = sorted_edges[edge_idx]
            dsu.union(u, v)
            edge_idx += 1
            
        results[orig_idx] = (dsu.num_components, dsu.max_component_size)
        
    return results