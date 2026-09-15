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
    Computes the Minimum Spanning Forest of a weighted undirected graph.
    
    :param num_vertices: Total number of vertices in the graph (0 to num_vertices - 1).
    :param edges: List of tuples (u, v, weight).
    :return: A tuple containing (total_cost, selected_edge_ids).
    """
    # Augment edges with original edge ID: (weight, original_id, u, v)
    augmented_edges = [
        (weight, edge_id, u, v) 
        for edge_id, (u, v, weight) in enumerate(edges)
    ]
    
    # Sort deterministically: primary by weight, secondary by original edge ID
    augmented_edges.sort(key=lambda x: (x[0], x[1]))

    dsu = DSU(num_vertices)
    total_cost = 0.0
    selected_edge_ids = []

    for weight, edge_id, u, v in augmented_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


# Example Usage:
if __name__ == "__main__":
    # Graph with 6 vertices and two disconnected components
    num_nodes = 6
    edge_list = [
        (0, 1, 4),  # Edge ID 0
        (0, 2, 4),  # Edge ID 1 (Equal weight to ID 0, ID 0 processed first)
        (1, 2, 2),  # Edge ID 2
        (3, 4, 3),  # Edge ID 3
        (4, 5, 1),  # Edge ID 4
        (3, 5, 5),  # Edge ID 5
    ]

    cost, selected_edges = minimum_spanning_forest(num_nodes, edge_list)
    print(f"Total MSF Cost: {cost}")
    print(f"Selected Edge IDs: {selected_edges}")