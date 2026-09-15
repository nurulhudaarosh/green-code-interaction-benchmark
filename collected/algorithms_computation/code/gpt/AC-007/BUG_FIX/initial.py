from typing import Iterable, List, Sequence, Tuple


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

        # Attach the smaller tree to the larger tree.
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a

        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]

        return True


def minimum_spanning_forest(
    n: int,
    edges: Sequence[Tuple[int, int, int, int]],
) -> Tuple[int, List[int]]:
    """
    Construct a minimum spanning forest using Kruskal's algorithm.

    Parameters
    ----------
    n:
        Number of vertices, numbered 0 through n - 1.

    edges:
        Sequence of edges in the form:
            (u, v, weight, edge_id)

        edge_id is the original ID of the edge.

    Returns
    -------
    (total_cost, selected_edge_ids)

        total_cost:
            Sum of the weights of all selected forest edges.

        selected_edge_ids:
            Original IDs of selected edges, in the order they
            were processed/selected by Kruskal.

    Raises
    ------
    ValueError:
        If n is negative or an endpoint is outside [0, n - 1].
    """
    if n < 0:
        raise ValueError("Number of vertices cannot be negative.")

    # Validate endpoints before processing.
    for u, v, _weight, _edge_id in edges:
        if not (0 <= u < n) or not (0 <= v < n):
            raise ValueError(
                f"Invalid edge endpoint: ({u}, {v}) for {n} vertices."
            )

    # Equal weights are resolved by original edge ID.
    sorted_edges = sorted(edges, key=lambda edge: (edge[2], edge[3]))

    dsu = DSU(n)

    total_cost = 0
    selected_edge_ids: List[int] = []

    for u, v, weight, edge_id in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids