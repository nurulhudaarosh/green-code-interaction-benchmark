class DSU:
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


def minimum_spanning_forest(num_vertices: int, edges: list[tuple[int, int, float | int]]) -> tuple[float | int, list[int]]:
    """
    Computes the Minimum Spanning Forest for an undirected weighted graph.

    :param num_vertices: Number of vertices in the graph (0 to num_vertices - 1).
    :param edges: List of tuples (u, v, weight) where original index represents Edge ID.
    :return: A tuple containing (total_cost, selected_edge_ids).
    """
    # Decorate edges with their original ID: (weight, edge_id, u, v)
    # Sorting tuple naturally handles weight ascending, then original edge_id ascending
    indexed_edges = [(weight, edge_id, u, v) for edge_id, (u, v, weight) in enumerate(edges)]
    indexed_edges.sort()

    dsu = DSU(num_vertices)
    total_cost = 0
    selected_edge_ids = []

    for weight, edge_id, u, v in indexed_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


# Example Usage
if __name__ == "__main__":
    # Graph with 6 vertices and disconnected components
    num_vertices = 6
    edges = [
        (0, 1, 4),  # Edge ID 0
        (0, 2, 4),  # Edge ID 1 (Same weight as ID 0, ID 0 processed first)
        (1, 2, 2),  # Edge ID 2
        (3, 4, 3),  # Edge ID 3
        (4, 5, 1),  # Edge ID 4
        (3, 5, 5),  # Edge ID 5
    ]

    cost, selected_ids = minimum_spanning_forest(num_vertices, edges)
    print(f"Total Cost: {cost}")
    print(f"Selected Edge IDs: {selected_ids}")