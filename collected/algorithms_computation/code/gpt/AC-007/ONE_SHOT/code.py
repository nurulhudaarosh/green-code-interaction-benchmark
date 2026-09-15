from typing import Iterable, List, Tuple


Edge = Tuple[int, int, int, int]
# Edge format: (u, v, weight, original_id)


class DSU:
    """Disjoint-Set Union with path compression and union by size."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        """Return the representative of x's component."""
        root = x

        while self.parent[root] != root:
            root = self.parent[root]

        # Path compression.
        while self.parent[x] != x:
            parent = self.parent[x]
            self.parent[x] = root
            x = parent

        return root

    def union(self, a: int, b: int) -> bool:
        """
        Merge the components containing a and b.

        Returns True if a merge happened, False if they were
        already in the same component.
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
    n: int,
    edges: Iterable[Edge],
) -> Tuple[int, List[int]]:
    """
    Construct a minimum spanning forest using Kruskal's algorithm.

    Parameters
    ----------
    n:
        Number of vertices, assumed to be labeled 0 through n - 1.

    edges:
        Iterable of edges represented as:
            (u, v, weight, original_id)

        The graph is undirected, so (u, v) and (v, u) represent
        the same connection.

    Returns
    -------
    (total_cost, selected_edge_ids)

        total_cost:
            Sum of the weights of all selected edges.

        selected_edge_ids:
            Original IDs of selected edges, in deterministic
            Kruskal selection order.
    """
    if n < 0:
        raise ValueError("Number of vertices cannot be negative.")

    # Materialize the edges so they can be sorted deterministically.
    edge_list = list(edges)

    # Validate endpoints.
    for u, v, weight, edge_id in edge_list:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(
                f"Invalid edge ({u}, {v}): vertices must be in [0, {n})."
            )

    # Equal-cost edges are processed by original ID.
    edge_list.sort(key=lambda edge: (edge[2], edge[3]))

    dsu = DSU(n)

    total_cost = 0
    selected_edge_ids: List[int] = []

    for u, v, weight, edge_id in edge_list:
        # Select the edge only if it connects two different components.
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


if __name__ == "__main__":
    # Example:
    #
    #   0 --1-- 1
    #   |       |
    #   4       2
    #   |       |
    #   2 --3-- 3
    #
    # Edge 4 is a more expensive alternative.

    edges = [
        (0, 1, 1, 10),
        (1, 3, 2, 20),
        (2, 3, 3, 30),
        (0, 2, 4, 40),
    ]

    cost, selected = minimum_spanning_forest(4, edges)

    print("Total cost:", cost)
    print("Selected edge IDs:", selected)

    # Expected:
    # Total cost: 6
    # Selected edge IDs: [10, 20, 30]