from typing import Iterable, Tuple, List, Hashable


class DSU:
    """Disjoint-Set Union / Union-Find with path compression and union by rank."""

    def __init__(self, vertices: Iterable[Hashable]):
        vertices = list(vertices)
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, x: Hashable) -> Hashable:
        # Path compression.
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: Hashable, b: Hashable) -> bool:
        """Merge two components. Return True if they were different."""
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

        # Union by rank.
        if self.rank[root_a] < self.rank[root_b]:
            root_a, root_b = root_b, root_a

        self.parent[root_b] = root_a

        if self.rank[root_a] == self.rank[root_b]:
            self.rank[root_a] += 1

        return True


def minimum_spanning_forest(
    vertices: Iterable[Hashable],
    edges: Iterable[Tuple[Hashable, Hashable, int, int]]
) -> Tuple[int, List[int]]:
    """
    Construct a minimum spanning forest using Kruskal's algorithm.

    Parameters
    ----------
    vertices:
        Iterable of vertex identifiers.

    edges:
        Iterable of edges in the form:
            (u, v, weight, edge_id)

        `edge_id` is the original ID of the edge.

    Returns
    -------
    (total_cost, selected_edge_ids)

        total_cost:
            Sum of weights of all selected edges.

        selected_edge_ids:
            Original IDs of selected edges, in deterministic
            Kruskal processing order.

    Tie-breaking
    ------------
    Edges are processed by:
        1. increasing weight
        2. increasing original edge ID
    """

    vertices = list(vertices)
    edges = list(edges)

    dsu = DSU(vertices)

    # Deterministic Kruskal ordering:
    # weight first, then original edge ID.
    edges.sort(key=lambda edge: (edge[2], edge[3]))

    total_cost = 0
    selected_edge_ids = []

    for u, v, weight, edge_id in edges:
        # Select the edge only if it connects two different components.
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


# ---------------------------------------------------------
# Example
# ---------------------------------------------------------

if __name__ == "__main__":
    vertices = [0, 1, 2, 3, 4]

    # (u, v, weight, original_edge_id)
    edges = [
        (0, 1, 4, 0),
        (0, 2, 1, 1),
        (1, 2, 2, 2),
        (1, 3, 5, 3),
        (2, 3, 3, 4),
        (3, 4, 1, 5),
    ]

    cost, selected_ids = minimum_spanning_forest(vertices, edges)

    print("Total cost:", cost)
    print("Selected edge IDs:", selected_ids)