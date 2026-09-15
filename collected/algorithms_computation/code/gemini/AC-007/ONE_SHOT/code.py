class DSU:
    """Disjoint-Set Union (Union-Find) with path compression and rank optimization."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)
        
        if root_i != root_j:
            # Union by rank
            if self.rank[root_i] < self.rank[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            if self.rank[root_i] == self.rank[root_j]:
                self.rank[root_i] += 1
            return True
        return False


def minimum_spanning_forest(num_vertices: int, edges: list[tuple[int, int, float]]) -> tuple[float, list[int]]:
    """
    Computes the Minimum Spanning Forest (MSF) of an undirected graph.
    
    :param num_vertices: Total number of vertices in the graph (0 to num_vertices - 1).
    :param edges: List of tuples (u, v, weight) where original_id is the index in this list.
    :return: A tuple containing (total_cost, sorted_list_of_selected_edge_ids).
    """
    # Decorate edges with original edge ID: (u, v, weight, original_id)
    indexed_edges = [
        (u, v, weight, edge_id) 
        for edge_id, (u, v, weight) in enumerate(edges)
    ]
    
    # Deterministic sort: Primary key = weight, Secondary key = edge_id
    indexed_edges.sort(key=lambda item: (item[2], item[3]))
    
    dsu = DSU(num_vertices)
    total_cost = 0.0
    selected_edge_ids = []
    
    for u, v, weight, edge_id in indexed_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)
            
    # Sort selected IDs for deterministic presentation
    selected_edge_ids.sort()
    
    return total_cost, selected_edge_ids


# Example Usage & Verification
if __name__ == "__main__":
    # Graph with 6 vertices and 2 disconnected components
    # Edges format: (u, v, weight)
    graph_edges = [
        (0, 1, 4),   # ID 0
        (0, 2, 4),   # ID 1 (Equal weight to ID 0, ID tie-breaker applies)
        (1, 2, 2),   # ID 2
        (2, 3, 3),   # ID 3
        (4, 5, 5),   # ID 4 (Component 2)
    ]
    
    n_vertices = 6
    cost, edge_ids = minimum_spanning_forest(n_vertices, graph_edges)
    
    print(f"Total MSF Cost: {cost}")
    print(f"Selected Edge IDs: {edge_ids}")