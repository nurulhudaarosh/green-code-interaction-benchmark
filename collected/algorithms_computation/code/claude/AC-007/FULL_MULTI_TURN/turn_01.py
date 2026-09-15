"""
Minimum Spanning Forest via Kruskal's Algorithm + Disjoint Set Union (DSU).

PROBLEM
-------
Given an undirected weighted graph (possibly disconnected), construct a
minimum spanning forest: a minimum-cost spanning tree for each connected
component. Return the total cost and the original IDs of the selected edges.

KEY CONSTRAINTS
----------------
1. Graph may be disconnected -> forest (multiple trees), not a single tree.
2. Equal-weight edges must be processed in ascending order of ORIGINAL edge ID
   (deterministic tie-breaking), not arbitrary/sort-unstable order.
3. Self-loops (u == v) can never help connectivity and must be ignored.
4. No randomness, network access, external services, or human interaction;
   standard library only.

REQUIRED OUTPUT
----------------
(total_cost, selected_edge_ids) where selected_edge_ids lists the original
IDs of edges chosen, in the order they were accepted.

ALGORITHM (Kruskal + DSU)
--------------------------
1. Sort edges by (weight, edge_id) ascending -> fixes tie-break rule.
2. Init DSU: each vertex its own set (path compression + union by rank).
3. Scan sorted edges; for each, if endpoints are in different sets, union
   them, add weight to total cost, record edge_id. Skip self-loops and
   edges that would form a cycle.
4. Stop when all components are internally connected (or edges exhausted).
   Complexity: O(E log E).
"""

from dataclasses import dataclass
from typing import Hashable, List, Sequence, Tuple


@dataclass(frozen=True)
class Edge:
    edge_id: int
    u: Hashable
    v: Hashable
    weight: float


class DisjointSetUnion:
    """Union-Find with union by rank and path compression."""

    def __init__(self, elements: Sequence[Hashable]):
        self._parent = {e: e for e in elements}
        self._rank = {e: 0 for e in elements}

    def find(self, x: Hashable) -> Hashable:
        root = x
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[x] != root:
            self._parent[x], x = root, self._parent[x]
        return root

    def union(self, a: Hashable, b: Hashable) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self._rank[ra] < self._rank[rb]:
            ra, rb = rb, ra
        self._parent[rb] = ra
        if self._rank[ra] == self._rank[rb]:
            self._rank[ra] += 1
        return True


def minimum_spanning_forest(
    vertices: Sequence[Hashable],
    edges: Sequence[Edge],
) -> Tuple[float, List[int]]:
    sorted_edges = sorted(edges, key=lambda e: (e.weight, e.edge_id))
    dsu = DisjointSetUnion(vertices)

    total_cost: float = 0
    selected_ids: List[int] = []
    remaining_components = len(set(vertices))
    if remaining_components == 0:
        return 0, []

    for e in sorted_edges:
        if remaining_components == 1:
            break
        if e.u == e.v:
            continue
        if dsu.union(e.u, e.v):
            total_cost += e.weight
            selected_ids.append(e.edge_id)
            remaining_components -= 1

    return total_cost, selected_ids


if __name__ == "__main__":
    vertices = list(range(6))  # vertex 5 isolated -> tests forest behavior
    edges = [
        Edge(0, 0, 1, 4),
        Edge(1, 0, 2, 4),
        Edge(2, 1, 2, 2),
        Edge(3, 1, 3, 5),
        Edge(4, 2, 3, 5),  # tie with edge 3 -> lower id (3) wins
        Edge(5, 3, 4, 3),
        Edge(6, 2, 4, 6),
    ]
    total_cost, chosen_ids = minimum_spanning_forest(vertices, edges)
    print("Total cost:", total_cost)
    print("Selected edge IDs:", chosen_ids)