class DisjointSetUnion:
    """Disjoint-Set Union (DSU) with path compression and rank optimization."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i: int) -> int:
        if self.parent[i] != i:
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
            - selected_edge_ids (list[int]): Edge IDs in the exact deterministic 
              order selected by Kruskal's algorithm.
    """
    # Deterministic sort: Primary key = weight ascending, Secondary key = edge_id ascending
    sorted_edges = sorted(edges, key=lambda x: (x[3], x[0]))

    dsu = DisjointSetUnion(num_vertices)
    total_cost = 0
    selected_edge_ids = []

    for edge_id, u, v, weight in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    # Return edge IDs in exact Kruskal selection sequence without post-hoc re-sorting
    return total_cost, selected_edge_ids


# Demonstration of Deterministic Tie-Handling & Correct Selection Trace
if __name__ == "__main__":
    num_nodes = 4
    # Equal-cost edges (weights 10) tie-broken strictly by edge_id:
    # Tuple format: (edge_id, u, v, weight)
    graph_edges = [
        (99, 0, 1, 10),  # weight 10, ID 99
        (12, 1, 2, 10),  # weight 10, ID 12 (should be evaluated before ID 99)
        (5,  2, 3, 2),   # weight 2,  ID 5  (should be evaluated first)
    ]

    cost, msf_edges = minimum_spanning_forest(num_nodes, graph_edges)

    print(f"Total MSF Cost: {cost}")
    print(f"Selected Edge IDs (In Order): {msf_edges}")
    # Output:
    # Total MSF Cost: 22
    # Selected Edge IDs (In Order): [5, 12, 99]