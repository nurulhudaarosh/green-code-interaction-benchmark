from typing import Iterable, List, Tuple


class DSU:
    """Disjoint Set Union with path compression and union by size."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        """Return the representative of x's component."""
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        """
        Merge the components containing a and b.

        Returns True if a merge happened, False if they
        were already in the same component.
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
    edges: Iterable[Tuple[int, int, int, int]]
) -> Tuple[int, List[int]]:
    """
    Construct a Minimum Spanning Forest using Kruskal's algorithm.

    Parameters
    ----------
    n:
        Number of vertices. Vertices are numbered 0 through n-1.

    edges:
        Iterable of tuples:
            (u, v, weight, original_edge_id)

        The graph is undirected.

    Returns
    -------
    (total_cost, selected_edge_ids)

    total_cost:
        Sum of the weights of all selected edges.

    selected_edge_ids:
        Original IDs of selected edges, in Kruskal processing order.

    Rules
    -----
    Edges are processed by:
        1. increasing weight
        2. increasing original edge ID for equal weights
    """

    if n < 0:
        raise ValueError("Number of vertices cannot be negative.")

    # Materialize the edges so they can be sorted.
    edge_list = list(edges)

    # Validate endpoints.
    for u, v, _, _ in edge_list:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(
                f"Invalid edge endpoint: ({u}, {v}) for n={n}"
            )

    # Kruskal tie-breaking:
    # first by weight, then by original edge ID.
    edge_list.sort(key=lambda edge: (edge[2], edge[3]))

    dsu = DSU(n)

    total_cost = 0
    selected_edge_ids: List[int] = []

    for u, v, weight, edge_id in edge_list:
        # Self-loops can never belong to an MST/MSF.
        if u == v:
            continue

        # Select the edge only if it connects different components.
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


# ------------------------------------------------------------
# Example
# ------------------------------------------------------------

if __name__ == "__main__":
    n = 5

    edges = [
        (0, 1, 4, 0),
        (0, 2, 1, 1),
        (1, 2, 2, 2),
        (1, 3, 5, 3),
        (2, 3, 3, 4),
        (3, 4, 2, 5),
    ]

    total_cost, selected_ids = minimum_spanning_forest(n, edges)

    print("Total cost:", total_cost)
    print("Selected edge IDs:", selected_ids)