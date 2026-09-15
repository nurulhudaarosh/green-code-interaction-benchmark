class DisjointSetUnion:
    """Disjoint-Set Union (DSU) / Union-Find with path compression and rank optimization."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        # Path compression
        self.parent[i] = self.find(self.parent[i])
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
    Computes the Minimum Spanning Forest using Kruskal's Algorithm.

    Args:
        num_vertices (int): Total number of vertices (0 to num_vertices - 1).
        edges (list of tuple): List of (u, v, weight) tuples.

    Returns:
        tuple: (total_cost, selected_edge_ids)
            - total_cost (float/int): Total weight of the forest.
            - selected_edge_ids (list of int): Sorted original edge IDs in the MSF.
    """
    if num_vertices <= 0:
        return 0, []

    # Attach original 0-indexed edge IDs
    # Form: (weight, original_id, u, v)
    indexed_edges = [(weight, idx, u, v) for idx, (u, v, weight) in enumerate(edges)]

    # Deterministic sort: Primary by weight (asc), Secondary by original edge ID (asc)
    indexed_edges.sort(key=lambda x: (x[0], x[1]))

    dsu = DisjointSetUnion(num_vertices)
    total_cost = 0
    selected_edge_ids = []

    for weight, original_id, u, v in indexed_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(original_id)

    # Sort selected IDs in ascending order for final presentation
    selected_edge_ids.sort()

    return total_cost, selected_edge_ids


# Example Execution
if __name__ == "__main__":
    # Graph with 2 disconnected components: (0-1-2) and (3-4)
    # Component 1: Vertices 0, 1, 2
    # Component 2: Vertices 3, 4
    # Disconnected Vertex: 5
    v_count = 6
    graph_edges = [
        (0, 1, 4),  # Edge ID 0
        (1, 2, 2),  # Edge ID 1
        (0, 2, 2),  # Edge ID 2 (Tied weight with ID 1; lower ID 1 selected first)
        (3, 4, 5),  # Edge ID 3
    ]

    cost, selected_ids = minimum_spanning_forest(v_count, graph_edges)
    print(f"Total MSF Cost: {cost}")
    print(f"Selected Edge IDs: {selected_ids}")