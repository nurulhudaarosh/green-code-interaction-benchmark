from typing import Iterable, List, Tuple


class DSU:
    """Disjoint Set Union / Union-Find with path compression and union by size."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        """Return the representative of x's set."""
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        """
        Merge the sets containing a and b.

        Returns True if a merge happened, otherwise False because
        both vertices were already in the same component.
        """
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

        # Union by size.
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a

        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]

        return True


def minimum_spanning_forest(
    num_vertices: int,
    edges: Iterable[Tuple[int, int, int, int]]
) -> Tuple[int, List[int]]:
    """
    Construct a minimum spanning forest using Kruskal's algorithm.

    Parameters
    ----------
    num_vertices:
        Number of vertices. Vertices must be numbered 0 through
        num_vertices - 1.

    edges:
        Iterable of edges in the form:
            (u, v, weight, edge_id)

        The edge_id is the original ID of the edge.

    Returns
    -------
    (total_cost, selected_edge_ids)

        total_cost:
            Sum of the weights of all selected edges.

        selected_edge_ids:
            Original IDs of the selected edges, in the deterministic
            Kruskal processing/selection order.

    Notes
    -----
    Equal-weight edges are processed by increasing original edge ID.
    """

    if num_vertices < 0:
        raise ValueError("num_vertices must be non-negative")

    # Convert to a list so that we can sort deterministically.
    edge_list = list(edges)

    # Validate vertices and edge IDs/weights enough to catch malformed input.
    for u, v, weight, edge_id in edge_list:
        if not (0 <= u < num_vertices):
            raise ValueError(f"Invalid vertex: {u}")
        if not (0 <= v < num_vertices):
            raise ValueError(f"Invalid vertex: {v}")

    # Kruskal ordering:
    #   1. Smaller weight first.
    #   2. For equal weights, smaller original edge ID first.
    edge_list.sort(key=lambda edge: (edge[2], edge[3]))

    dsu = DSU(num_vertices)

    total_cost = 0
    selected_edge_ids = []

    for u, v, weight, edge_id in edge_list:
        # Select the edge only if it connects two different components.
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


# ---------------------------------------------------------
# Example
# ---------------------------------------------------------

if __name__ == "__main__":
    # Edge format:
    # (u, v, weight, original_edge_id)
    edges = [
        (0, 1, 4, 10),
        (0, 2, 1, 11),
        (1, 2, 2, 12),
        (1, 3, 3, 13),
        (2, 3, 5, 14),
        (4, 5, 7, 15),  # Separate component
    ]

    total_cost, selected_edge_ids = minimum_spanning_forest(
        num_vertices=6,
        edges=edges
    )

    print("Total cost:", total_cost)
    print("Selected edge IDs:", selected_edge_ids)