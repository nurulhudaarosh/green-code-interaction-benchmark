class DisjointSetUnion:
    """Disjoint Set Union (DSU) tracking component count and max size."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_component_size = 1 if n > 0 else 0

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i != root_j:
            # Union by size
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            
            self.num_components -= 1
            if self.size[root_i] > self.max_component_size:
                self.max_component_size = self.size[root_i]
            return True
        return False


def query_components_by_threshold(n: int, edges: list[tuple[int, int, int]], queries: list[int]) -> list[tuple[int, int]]:
    """
    Evaluates graph components for each weight threshold query.
    
    :param n: Number of vertices (0 to n-1)
    :param edges: List of tuples (u, v, weight)
    :param queries: List of query thresholds q
    :return: List of tuples (num_components, max_component_size) matching query order
    """
    # Sort edges by weight
    sorted_edges = sorted(edges, key=lambda e: e[2])
    
    # Pair queries with their original indices and sort by threshold
    indexed_queries = sorted(enumerate(queries), key=lambda x: x[1])
    
    dsu = DisjointSetUnion(n)
    results = [None] * len(queries)
    
    edge_idx = 0
    num_edges = len(sorted_edges)

    for orig_idx, threshold in indexed_queries:
        # Incrementally add edges with weight <= threshold
        while edge_idx < num_edges and sorted_edges[edge_idx][2] <= threshold:
            u, v, w = sorted_edges[edge_idx]
            dsu.union(u, v)
            edge_idx += 1
        
        results[orig_idx] = (dsu.num_components, dsu.max_component_size)

    return results


# Example Usage
if __name__ == "__main__":
    n = 5
    # Edges format: (u, v, weight)
    edges = [
        (0, 1, 2),
        (1, 2, 4),
        (2, 3, 1),
        (3, 4, 5)
    ]
    queries = [0, 2, 3, 5]

    res = query_components_by_threshold(n, edges, queries)
    for q, (comps, max_size) in zip(queries, res):
        print(f"Threshold <= {q}: Components = {comps}, Max Size = {max_size}")