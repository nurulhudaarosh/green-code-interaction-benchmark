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
        """Merge two components. Return True if they were different."""
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
    Return the total cost and selected original edge IDs
    of a Minimum Spanning Forest.

    Each edge is:
        (u, v, weight, original_edge_id)

    Tie-breaking:
        smaller weight first;
        for equal weights, smaller original_edge_id first.
    """

    if n < 0:
        raise ValueError("Number of vertices cannot be negative.")

    edge_list = list(edges)

    # Validate endpoints.
    for u, v, _, _ in edge_list:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(
                f"Invalid edge endpoint: ({u}, {v}) for n={n}"
            )

    # FIX:
    # Kruskal must process equal-weight edges by original ID.
    edge_list.sort(key=lambda edge: (edge[2], edge[3]))

    dsu = DSU(n)

    total_cost = 0
    selected_edge_ids: List[int] = []

    for u, v, weight, edge_id in edge_list:
        # A self-loop can never be part of an MSF.
        if u == v:
            continue

        # Select only edges connecting different components.
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


# ------------------------------------------------------------
# Tests demonstrating deterministic tie handling
# ------------------------------------------------------------

def test_equal_weight_tie_breaking() -> None:
    """
    All edges have equal weight, but the input order is deliberately
    different from the required original-ID order.
    """
    edges = [
        (0, 2, 1, 2),
        (1, 2, 1, 1),
        (0, 1, 1, 0),
    ]

    result = minimum_spanning_forest(3, edges)

    assert result == (2, [0, 1])


def test_normal_kruskal_case() -> None:
    edges = [
        (0, 1, 4, 0),
        (0, 2, 1, 1),
        (1, 2, 2, 2),
        (1, 3, 5, 3),
        (2, 3, 3, 4),
        (3, 4, 2, 5),
    ]

    result = minimum_spanning_forest(5, edges)

    assert result == (8, [1, 2, 5, 4])


def test_disconnected_graph() -> None:
    """
    Two connected components:
        0--1
        2--3
    """
    edges = [
        (0, 1, 5, 0),
        (2, 3, 2, 1),
    ]

    result = minimum_spanning_forest(4, edges)

    assert result == (7, [1, 0])


def test_cycle_is_skipped() -> None:
    edges = [
        (0, 1, 1, 0),
        (1, 2, 1, 1),
        (0, 2, 1, 2),
    ]

    result = minimum_spanning_forest(3, edges)

    assert result == (2, [0, 1])


if __name__ == "__main__":
    test_equal_weight_tie_breaking()
    test_normal_kruskal_case()
    test_disconnected_graph()
    test_cycle_is_skipped()

    print("All tests passed.")