class DisjointSetUnion:
    """Disjoint-Set Union (DSU) / Union-Find structure with path compression and rank optimization."""
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


def minimum_spanning_forest(num_vertices: int, edges: list[tuple[int, int, int, int]]) -> tuple[int, list[int]]:
    """
    Computes the Minimum Spanning Forest (MSF) of an undirected weighted graph.

    Parameters:
        num_vertices (int): Total number of vertices (0-indexed).
        edges (list of tuple): List of edges, where each edge is specified as 
                              (edge_id, u, v, weight).

    Returns:
        tuple[int, list[int]]:
            - total_cost (int): Total weight of the MSF.
            - selected_edge_ids (list[int]): Sorted list of original IDs of the selected edges.
    """
    # Sort edges primarily by weight ascending, secondarily by edge_id ascending
    sorted_edges = sorted(edges, key=lambda x: (x[3], x[0]))

    dsu = DisjointSetUnion(num_vertices)
    total_cost = 0
    selected_edge_ids = []

    for edge_id, u, v, weight in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    # Sort selected edge IDs for consistent output ordering
    selected_edge_ids.sort()

    return total_cost, selected_edge_ids


# Example Usage
if __name__ == "__main__":
    # 6 vertices (0 to 5), disconnected graph with two components: {0, 1, 2} and {3, 4, 5}
    # Edge tuple format: (edge_id, u, v, weight)
    graph_edges = [
        (0, 0, 1, 4),
        (1, 1, 2, 2),
        (2, 0, 2, 2),  # Tie in weight with edge 1, resolved by edge_id
        (3, 3, 4, 5),
        (4, 4, 5, 1),
        (5, 3, 5, 5),  # Tie in weight with edge 3, resolved by edge_id
    ]
    num_nodes = 6

    cost, msf_edges = minimum_spanning_forest(num_nodes, graph_edges)

    print(f"Total MSF Cost: {cost}")
    print(f"Selected Edge IDs: {msf_edges}")