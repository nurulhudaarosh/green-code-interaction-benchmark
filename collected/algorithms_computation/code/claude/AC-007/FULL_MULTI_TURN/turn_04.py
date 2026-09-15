"""
Minimum Spanning Forest via Kruskal's Algorithm + Disjoint Set Union (DSU).

PROBLEM
-------
Given an undirected weighted graph (possibly disconnected), construct a
minimum spanning forest: a minimum-cost spanning tree for each connected
component. Return the total cost and the original IDs of the selected edges.

REQUIRED OUTPUTS (always present)
-----------------------------------
1. total_cost         — sum of weights of selected edges.
2. selected_edge_ids  — original IDs of edges chosen, in acceptance order.

OPTIONAL OUTPUT (only when include_operation_summary=True)
------------------------------------------------------------
3. operation_summary  — dict of deterministic counts of the algorithm's
   major decisions: edges_considered, self_loops_skipped, cycle_rejections,
   unions_performed, total_decisions. Absent entirely when the flag is False
   (default) — all other behavior, fields, and values unchanged.

KEY CONSTRAINTS
----------------
1. Graph may be disconnected -> forest, not a single tree.
2. Equal-weight edges processed in ascending original-ID order.
3. Self-loops (u == v) ignored (never contribute to connectivity).
4. Standard library only; no randomness, network, external services, or
   human interaction. Fully deterministic: same input -> same output always.

BOUNDARY CASES EXPLICITLY HANDLED
------------------------------------
- Zero vertices / zero edges.
- Single vertex, with or without self-loops.
- Fully disconnected graphs (no edges at all).
- Duplicate/parallel edges with tied weights.
- Negative and zero edge weights.
- Very large edge weights.
- Edge list given out of any particular order.

ALGORITHM (Kruskal + DSU)
--------------------------
1. Sort edges by (weight, edge_id) ascending — fixes tie handling.
2. Init DSU: each vertex its own set (path compression + union by rank).
3. Scan sorted edges; skip self-loops, else attempt union. Success -> select
   edge, add cost. Failure (same component) -> reject as a cycle.
4. Stop once every component is fully connected, or edges are exhausted.
   Complexity: O(E log E).
"""

from dataclasses import dataclass
from typing import Hashable, List, Sequence, Tuple, Union
import unittest


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


def _tie_break_key(edge: Edge) -> Tuple[float, int]:
    """Deterministic Kruskal ordering key: weight first, original ID breaks ties."""
    return (edge.weight, edge.edge_id)


def minimum_spanning_forest(
    vertices: Sequence[Hashable],
    edges: Sequence[Edge],
    include_operation_summary: bool = False,
) -> Union[Tuple[float, List[int]], Tuple[float, List[int], dict]]:
    vertex_set = set(vertices)
    for e in edges:
        if e.u not in vertex_set or e.v not in vertex_set:
            raise ValueError(f"Edge {e.edge_id} references a vertex not in 'vertices'")

    sorted_edges = sorted(edges, key=_tie_break_key)
    dsu = DisjointSetUnion(vertex_set)

    total_cost: float = 0
    selected_ids: List[int] = []
    remaining_components = len(vertex_set)

    edges_considered = 0
    self_loops_skipped = 0
    cycle_rejections = 0

    if remaining_components == 0:
        if include_operation_summary:
            summary = {
                "edges_considered": 0,
                "self_loops_skipped": 0,
                "cycle_rejections": 0,
                "unions_performed": 0,
                "total_decisions": 0,
            }
            return 0, [], summary
        return 0, []

    for e in sorted_edges:
        if remaining_components == 1:
            break
        edges_considered += 1
        if e.u == e.v:
            self_loops_skipped += 1
            continue
        if dsu.union(e.u, e.v):
            total_cost += e.weight
            selected_ids.append(e.edge_id)
            remaining_components -= 1
        else:
            cycle_rejections += 1

    if include_operation_summary:
        summary = {
            "edges_considered": edges_considered,
            "self_loops_skipped": self_loops_skipped,
            "cycle_rejections": cycle_rejections,
            "unions_performed": len(selected_ids),
            "total_decisions": edges_considered,
        }
        return total_cost, selected_ids, summary

    return total_cost, selected_ids


class TestMinimumSpanningForestBoundaries(unittest.TestCase):

    def test_empty_graph_no_vertices_no_edges(self):
        self.assertEqual(minimum_spanning_forest([], []), (0, []))

    def test_single_vertex_no_edges(self):
        self.assertEqual(minimum_spanning_forest([0], []), (0, []))

    def test_single_vertex_with_self_loops_ignored(self):
        edges = [Edge(0, 0, 0, 5), Edge(1, 0, 0, -3)]
        self.assertEqual(minimum_spanning_forest([0], edges), (0, []))

    def test_multiple_vertices_no_edges_fully_disconnected(self):
        vertices = [0, 1, 2, 3]
        self.assertEqual(minimum_spanning_forest(vertices, []), (0, []))

    def test_all_vertices_isolated_edges_list_present_elsewhere(self):
        # Edges only reference a subset; remaining vertices stay isolated.
        vertices = [0, 1, 2, 3, 4]
        edges = [Edge(0, 0, 1, 2)]
        cost, ids = minimum_spanning_forest(vertices, edges)
        self.assertEqual((cost, ids), (2, [0]))

    def test_single_edge_minimal_nontrivial_case(self):
        vertices = [0, 1]
        edges = [Edge(0, 0, 1, 7)]
        self.assertEqual(minimum_spanning_forest(vertices, edges), (7, [0]))

    def test_complete_graph_all_equal_weights_tie_break_by_id(self):
        # K4 with every edge weight = 1; must pick exactly 3 edges,
        # deterministically the lowest IDs that don't form a cycle.
        vertices = [0, 1, 2, 3]
        edges = [
            Edge(0, 0, 1, 1),
            Edge(1, 0, 2, 1),
            Edge(2, 0, 3, 1),
            Edge(3, 1, 2, 1),
            Edge(4, 1, 3, 1),
            Edge(5, 2, 3, 1),
        ]
        cost, ids = minimum_spanning_forest(vertices, edges)
        self.assertEqual(cost, 3)
        # Kruskal in id order 0,1,2,... : 0(0-1) ok,1(0-2) ok,2(0-3) ok,
        # then 3,4,5 all form cycles -> rejected.
        self.assertEqual(ids, [0, 1, 2])

    def test_negative_weight_edges_are_preferred(self):
        vertices = [0, 1, 2]
        edges = [
            Edge(0, 0, 1, -10),
            Edge(1, 1, 2, 5),
            Edge(2, 0, 2, 100),
        ]
        cost, ids = minimum_spanning_forest(vertices, edges)
        self.assertEqual((cost, ids), (-5, [0, 1]))

    def test_zero_weight_edges(self):
        vertices = [0, 1, 2]
        edges = [Edge(0, 0, 1, 0), Edge(1, 1, 2, 0)]
        self.assertEqual(minimum_spanning_forest(vertices, edges), (0, [0, 1]))

    def test_duplicate_parallel_edges_tie_break_lowest_id_wins(self):
        # Three parallel edges between the same pair, same weight.
        # Lowest id is accepted; the rest are cycle-rejections.
        vertices = [0, 1]
        edges = [
            Edge(7, 0, 1, 3),
            Edge(2, 0, 1, 3),
            Edge(9, 0, 1, 3),
        ]
        cost, ids = minimum_spanning_forest(vertices, edges)
        self.assertEqual((cost, ids), (3, [2]))

    def test_very_large_weight_values_no_overflow(self):
        big = 10**18
        vertices = [0, 1, 2]
        edges = [Edge(0, 0, 1, big), Edge(1, 1, 2, big + 1)]
        cost, ids = minimum_spanning_forest(vertices, edges)
        self.assertEqual((cost, ids), (2 * big + 1, [0, 1]))

    def test_edge_list_out_of_order_still_deterministic(self):
        # Same logical graph as the tie-break test, but shuffled input order
        # (fixed shuffle, not random) — result must be identical.
        vertices = [0, 1, 2]
        edges_forward = [Edge(1, 1, 2, 1), Edge(0, 0, 1, 1), Edge(2, 0, 2, 1)]
        edges_reordered = [Edge(2, 0, 2, 1), Edge(1, 1, 2, 1), Edge(0, 0, 1, 1)]
        self.assertEqual(
            minimum_spanning_forest(vertices, edges_forward),
            minimum_spanning_forest(vertices, edges_reordered),
        )

    def test_operation_summary_still_works_on_boundary_empty_graph(self):
        cost, ids, summary = minimum_spanning_forest(
            [], [], include_operation_summary=True
        )
        self.assertEqual((cost, ids), (0, []))
        self.assertEqual(summary["total_decisions"], 0)

    def test_default_output_shape_unchanged_when_flag_omitted(self):
        result = minimum_spanning_forest([0, 1], [Edge(0, 0, 1, 4)])
        self.assertEqual(len(result), 2)  # exactly (total_cost, selected_edge_ids)


if __name__ == "__main__":
    unittest.main(verbosity=2)