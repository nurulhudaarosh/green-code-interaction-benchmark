from typing import Iterable, Tuple, List, Hashable, Dict, Union


class DSU:
    """Disjoint-Set Union with path compression and union by rank."""

    def __init__(self, vertices: Iterable[Hashable]):
        vertices = list(vertices)
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, x: Hashable) -> Hashable:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: Hashable, b: Hashable) -> bool:
        """Return True if a and b were in different components."""
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

        if self.rank[root_a] < self.rank[root_b]:
            root_a, root_b = root_b, root_a

        self.parent[root_b] = root_a

        if self.rank[root_a] == self.rank[root_b]:
            self.rank[root_a] += 1

        return True


def minimum_spanning_forest(
    vertices: Iterable[Hashable],
    edges: Iterable[Tuple[Hashable, Hashable, int, int]],
    include_operation_summary: bool = False
) -> Union[
    Tuple[int, List[int]],
    Tuple[int, List[int], Dict[str, int]]
]:
    """
    Construct a Minimum Spanning Forest using Kruskal's algorithm.

    Edge format:
        (u, v, weight, edge_id)

    Edges are processed by:
        1. increasing weight
        2. increasing original edge_id

    Original output:
        (total_cost, selected_edge_ids)

    If include_operation_summary=True:
        (total_cost, selected_edge_ids, operation_summary)

    operation_summary contains:
        - edges_considered
        - edges_selected
        - edges_skipped
    """

    vertices = list(vertices)
    edges = list(edges)

    dsu = DSU(vertices)

    # Deterministic Kruskal ordering.
    edges.sort(key=lambda edge: (edge[2], edge[3]))

    total_cost = 0
    selected_edge_ids = []

    # New feature: deterministic operation counters.
    edges_considered = 0
    edges_selected = 0
    edges_skipped = 0

    for u, v, weight, edge_id in edges:
        edges_considered += 1

        # If union succeeds, the edge connects two
        # different components and is therefore selected.
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)
            edges_selected += 1
        else:
            # The edge would create a cycle.
            edges_skipped += 1

    # Preserve the original output exactly when the
    # optional feature is not requested.
    if not include_operation_summary:
        return total_cost, selected_edge_ids

    operation_summary = {
        "edges_considered": edges_considered,
        "edges_selected": edges_selected,
        "edges_skipped": edges_skipped,
    }

    return total_cost, selected_edge_ids, operation_summary


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

    # Original behavior: exactly two fields.
    cost, selected_ids = minimum_spanning_forest(
        vertices,
        edges
    )

    print(cost)
    print(selected_ids)

    # New behavior: three fields including operation_summary.
    cost, selected_ids, operation_summary = minimum_spanning_forest(
        vertices,
        edges,
        include_operation_summary=True
    )

    print(cost)
    print(selected_ids)
    print(operation_summary)