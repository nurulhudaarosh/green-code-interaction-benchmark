class DSU:
    """Disjoint-Set Union with path compression and rank optimization."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.num_components = n

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            if self.rank[root_i] == self.rank[root_j]:
                self.rank[root_i] += 1
            self.num_components -= 1
            return True
        return False


def minimum_spanning_forest(
    num_vertices: int, 
    edges: list[tuple[int, int, float]], 
    include_summary: bool = False
) -> tuple[float, list[int]] | tuple[float, list[int], dict]:
    """
    Computes the Minimum Spanning Forest of a weighted undirected graph.
    
    :param num_vertices: Total number of vertices in the graph.
    :param edges: List of tuples (u, v, weight).
    :param include_summary: If True, returns an additional `operation_summary` dictionary.
    :return: (total_cost, selected_edge_ids) if include_summary is False,
             or (total_cost, selected_edge_ids, operation_summary) if True.
    """
    # Augment edges with original ID: (weight, original_id, u, v)
    augmented_edges = [
        (weight, edge_id, u, v) 
        for edge_id, (u, v, weight) in enumerate(edges)
    ]
    
    # Sort deterministically: primary by weight, secondary by original ID
    augmented_edges.sort(key=lambda x: (x[0], x[1]))

    dsu = DSU(num_vertices)
    total_cost = 0.0
    selected_edge_ids = []
    
    edges_evaluated = 0
    dsu_unions_performed = 0
    dsu_cycles_rejected = 0

    for weight, edge_id, u, v in augmented_edges:
        edges_evaluated += 1
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)
            dsu_unions_performed += 1
        else:
            dsu_cycles_rejected += 1

    if include_summary:
        operation_summary = {
            "edges_evaluated": edges_evaluated,
            "dsu_unions_performed": dsu_unions_performed,
            "dsu_cycles_rejected": dsu_cycles_rejected,
            "components_remaining": dsu.num_components,
        }
        return total_cost, selected_edge_ids, operation_summary

    return total_cost, selected_edge_ids


# Example Usage:
if __name__ == "__main__":
    num_nodes = 6
    edge_list = [
        (0, 1, 4),  # Edge 0
        (0, 2, 4),  # Edge 1
        (1, 2, 2),  # Edge 2
        (3, 4, 3),  # Edge 3
        (4, 5, 1),  # Edge 4
        (3, 5, 5),  # Edge 5
    ]

    # Standard invocation (unchanged contract)
    cost, selected_edges = minimum_spanning_forest(num_nodes, edge_list)
    print("Default Output:")
    print(f"  Cost: {cost}, Selected Edges: {selected_edges}\n")

    # Invocations requesting operation summary
    cost, selected_edges, summary = minimum_spanning_forest(num_nodes, edge_list, include_summary=True)
    print("Extended Output:")
    print(f"  Cost: {cost}")
    print(f"  Selected Edges: {selected_edges}")
    print(f"  Operation Summary: {summary}")