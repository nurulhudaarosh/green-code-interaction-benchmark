"""
PROBLEM
-------
Given an undirected weighted graph (possibly disconnected), construct a
minimum spanning forest (an MST for each connected component) and return:
  1. Its total cost (sum of the weights of the selected edges).
  2. The original IDs of the selected edges.
Equal-weight edges must be processed in ascending order of their original
ID, so results — including internal tie-breaking — are fully reproducible
regardless of input ordering or edge endpoint order.

KEY CONSTRAINTS
----------------
- Graph is undirected and weighted; may be disconnected -> result is a
  forest, not necessarily a single spanning tree.
- Each edge carries an original ID that must be preserved in the output.
- Ties in weight are broken deterministically by ascending original ID.
- The disjoint-set union structure itself must resolve ties (equal rank)
  deterministically based on vertex ID, not on argument/call order.
- No randomness, network access, external services, or human interaction;
  standard library only.

REQUIRED OUTPUT
----------------
- total_cost: sum of weights of edges chosen for the minimum spanning forest.
- selected_edge_ids: sorted list of original IDs of the chosen edges.

ALGORITHM
---------
Kruskal's algorithm with a Disjoint-Set Union (DSU / Union-Find):
1. Sort edges by (weight, original_id) ascending for determinism.
2. Initialize DSU with one set per vertex.
3. For each edge in sorted order, if its endpoints are in different sets,
   union them (breaking equal-rank ties by smaller vertex/root ID, so the
   resulting DSU shape never depends on call argument order) and select
   the edge; otherwise skip it (it would create a cycle).
4. Continue until all edges are processed (or the forest is fully formed).
5. Return the total cost and the sorted list of selected edge IDs.
"""

from typing import List, NamedTuple, Tuple


class Edge(NamedTuple):
    id: int
    u: int
    v: int
    weight: float


class DSU:
    """Disjoint-Set Union with path compression and union by rank.

    Equal-rank ties are broken by always attaching the numerically larger
    root under the smaller root, so the resulting tree shape depends only
    on vertex IDs — never on which argument order union() was called with.
    """

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        elif self.rank[ra] == self.rank[rb]:
            # Deterministic tie-break: smaller root ID becomes the parent,
            # regardless of which argument (a or b) it came from.
            if rb < ra:
                ra, rb = rb, ra
            self.rank[ra] += 1
        self.parent[rb] = ra
        return True


def minimum_spanning_forest(
    num_vertices: int,
    edges: List[Tuple[int, int, int, float]],
) -> Tuple[float, List[int]]:
    """
    Args:
        num_vertices: number of vertices, labeled 0..num_vertices-1.
        edges: list of (edge_id, u, v, weight) tuples; edge_id is unique.

    Returns:
        (total_cost, selected_edge_ids)
    """
    if num_vertices < 0:
        raise ValueError("num_vertices must be non-negative")

    parsed_edges = [Edge(eid, u, v, w) for (eid, u, v, w) in edges]

    for e in parsed_edges:
        if not (0 <= e.u < num_vertices) or not (0 <= e.v < num_vertices):
            raise ValueError(f"Edge {e.id} references a vertex out of range")

    # Deterministic order: primary key = weight, secondary key = original id.
    parsed_edges.sort(key=lambda e: (e.weight, e.id))

    dsu = DSU(num_vertices)
    total_cost = 0
    selected_ids: List[int] = []
    edges_needed = max(num_vertices - 1, 0)

    for e in parsed_edges:
        if len(selected_ids) == edges_needed:
            break
        if dsu.union(e.u, e.v):
            total_cost += e.weight
            selected_ids.append(e.id)

    selected_ids.sort()
    return total_cost, selected_ids


if __name__ == "__main__":
    num_vertices = 6
    sample_edges = [
        (1, 0, 1, 4),
        (2, 1, 2, 4),
        (3, 0, 2, 8),
        (4, 2, 3, 7),
        (5, 3, 4, 4),
        (6, 1, 3, 9),
        (7, 2, 4, 2),
        # vertex 5 stays isolated -> forest, not a single tree
    ]

    cost, chosen_ids = minimum_spanning_forest(num_vertices, sample_edges)
    print(f"Total cost: {cost}")
    print(f"Selected edge IDs: {chosen_ids}")

    # Regression check for the bug: endpoint order must not affect DSU shape
    tie_edges_a = [(1, 0, 1, 5), (2, 2, 3, 5), (3, 1, 2, 5)]
    tie_edges_b = [(1, 0, 1, 5), (2, 2, 3, 5), (3, 2, 1, 5)]  # edge 3 endpoints swapped
    assert minimum_spanning_forest(4, tie_edges_a) == minimum_spanning_forest(4, tie_edges_b)