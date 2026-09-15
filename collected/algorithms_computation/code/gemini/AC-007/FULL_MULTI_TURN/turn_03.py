class DisjointSetUnion:
    """Disjoint-Set Union (DSU) with path compression and rank optimization."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.find_count = 0

    def find(self, i: int) -> int:
        self.find_count += 1
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


def minimum_spanning_forest(
    num_vertices: int,
    edges: list[tuple[int, int, int, int]],
    return_summary: bool = False,
) -> tuple[int, list[int]] | tuple[int, list[int], dict[str, int]]:
    """Computes the Minimum Spanning Forest (MSF) of an undirected weighted graph.

    Parameters:
        num_vertices (int): Total number of vertices (0-indexed).
        edges (list of tuple): List of edges as (edge_id, u, v, weight).
        return_summary (bool): If True, returns an additional
          `operation_summary` dict.

    Returns:
        If return_summary is False:
            (total_cost, selected_edge_ids)
        If return_summary is True:
            (total_cost, selected_edge_ids, operation_summary)
    """
    # Deterministic sort: Primary key = weight ascending, Secondary key = edge_id ascending
    sorted_edges = sorted(edges, key=lambda x: (x[3], x[0]))

    dsu = DisjointSetUnion(num_vertices)
    total_cost = 0
    selected_edge_ids = []

    edges_processed = 0
    edges_rejected = 0

    for edge_id, u, v, weight in sorted_edges:
        edges_processed += 1
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)
        else:
            edges_rejected += 1

    if return_summary:
        summary = {
            "edges_processed": edges_processed,
            "dsu_find_calls": dsu.find_count,
            "dsu_unions_attempted": edges_processed,
            "edges_accepted": len(selected_edge_ids),
            "edges_rejected": edges_rejected,
        }
        return total_cost, selected_edge_ids, summary

    return total_cost, selected_edge_ids


# Demonstration & Verification
if __name__ == "__main__":
    num_nodes = 4
    # Format: (edge_id, u, v, weight)
    graph_edges = [
        (0, 0, 1, 3),
        (1, 1, 2, 2),
        (2, 0, 2, 2),  # Weight tie with edge 1; resolved deterministically by edge_id (1 < 2)
        (3, 2, 3, 4),
    ]

    # Standard call (backwards compatible)
    cost, msf_edges = minimum_spanning_forest(num_nodes, graph_edges)
    print("Standard Call Output:")
    print(f"  Total Cost: {cost}")
    print(f"  Selected Edge IDs: {msf_edges}\n")

    # Extended call with summary
    cost, msf_edges, summary = minimum_spanning_forest(
        num_nodes, graph_edges, return_summary=True
    )
    print("Extended Call Output (return_summary=True):")
    print(f"  Total Cost: {cost}")
    print(f"  Selected Edge IDs: {msf_edges}")
    print(f"  Operation Summary: {summary}")