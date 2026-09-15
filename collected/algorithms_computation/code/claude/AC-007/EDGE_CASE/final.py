"""
PROBLEM RESTATEMENT
====================
Given an undirected weighted graph G = (V, E), where each edge has an
original ID (its position/index in the input edge list) and a numeric
weight, construct a Minimum Spanning Forest (MSF):
  - For every connected component of G, select a subset of its edges
    that forms a spanning tree of that component with minimum total
    weight.
  - If G is disconnected, the result is a forest: one MST per
    component, unioned together.
  - If G has isolated vertices (no incident edges), they still belong
    to the vertex set but contribute no edges to the forest.

Return:
  1. total_cost: the sum of the weights of all selected edges.
  2. selected_edge_ids: the original IDs of the selected edges, in the
     order they were added while running Kruskal's algorithm.

Tie-breaking rule (must be preserved exactly):
  Edges are processed in ascending order of (weight, original_id).
  This means among edges of equal weight, the one with the smaller
  original ID is always considered first. This guarantees a single
  deterministic, reproducible output regardless of input ordering
  quirks, dict iteration order, or the underlying sort algorithm.

BOUNDARY / EDGE CASES TO HANDLE EXPLICITLY
============================================
1. Empty graph: no vertices, no edges -> total_cost = 0, selected = [].
2. Single vertex, no edges -> total_cost = 0, selected = [] (trivial
   tree with 0 edges).
3. Vertices present but zero edges (all isolated) -> total_cost = 0,
   selected = [] (forest of singleton trees).
4. Self-loop edges (u == v) -> must be skipped entirely; they can
   never be part of any spanning tree and must not raise errors or
   affect the DSU.
5. Duplicate / parallel edges between the same pair of vertices
   (including identical weights) -> only the cheapest ones needed for
   connectivity are picked; redundant ones are skipped via DSU cycle
   detection, tie-broken by original ID like any other edge.
6. All edges having the exact same weight -> selection must degrade
   into "sort purely by original ID" and still yield a correct
   spanning forest.
7. Negative, zero, and floating-point weights -> algorithm must treat
   these uniformly; Kruskal's correctness does not depend on
   non-negativity.
8. Already-disconnected graph with multiple components -> must return
   a valid forest (one MST per component), not attempt to force full
   connectivity.
9. Large original edge IDs / large vertex label space -> correctness
   should not depend on IDs being contiguous or starting at 0.
10. A single edge connecting two vertices with equal weight to itself
    duplicated many times -> only one is chosen (lowest ID among the
    ties), rest skipped as cycles.

All of the above preserve the original output contract:
    (total_cost, selected_edge_ids)
and the original tie-breaking rule: ascending (weight, original_id).
"""

from typing import List, Tuple, Sequence, Hashable, Union
import unittest


class DSU:
    """Disjoint Set Union (Union-Find) with path compression and union by rank."""

    def __init__(self, vertices: Sequence[Hashable]):
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, x: Hashable) -> Hashable:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: Hashable, b: Hashable) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False  # already connected -> would form a cycle
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def minimum_spanning_forest(
    vertices: Sequence[Hashable],
    edges: Sequence[Tuple[Hashable, Hashable, Union[int, float]]],
) -> Tuple[Union[int, float], List[int]]:
    """
    Compute a deterministic Minimum Spanning Forest via Kruskal's algorithm.

    Parameters
    ----------
    vertices : sequence of hashable vertex labels (all vertices in the
               graph, including isolated ones). May be empty.
    edges    : sequence of (u, v, weight) tuples. The original edge ID
               of edges[i] is its index i in this sequence. May be empty.

    Returns
    -------
    (total_cost, selected_edge_ids)
        total_cost         : sum of weights of the selected MSF edges
                              (0 if no edges are selected).
        selected_edge_ids  : original indices of selected edges, in the
                              order they were added to the forest.
    """
    # --- Boundary case: no vertices at all -> nothing to do. ---
    unique_vertices = set(vertices)
    if not unique_vertices:
        return 0, []

    # --- Boundary case: vertices exist but no edges given at all. ---
    if not edges:
        return 0, []

    # Attach original IDs (their position in the input list) to each edge.
    indexed_edges = [
        (w, edge_id, u, v) for edge_id, (u, v, w) in enumerate(edges)
    ]

    # Deterministic ordering: ascending weight, then ascending original ID.
    # This single sort key handles the "all weights equal" boundary case
    # correctly too, since it then degenerates to sorting by ID alone.
    indexed_edges.sort(key=lambda e: (e[0], e[1]))

    dsu = DSU(unique_vertices)

    total_cost: Union[int, float] = 0
    selected_edge_ids: List[int] = []

    num_components_remaining = len(unique_vertices)

    for w, edge_id, u, v in indexed_edges:
        if num_components_remaining == 1:
            break  # already fully connected; no edge can help further

        # --- Boundary case: self-loop -> never valid, always skip. ---
        if u == v:
            continue

        # Vertices referenced by an edge but absent from `vertices` are
        # tolerated by adding them lazily, keeping the function robust
        # to slightly inconsistent input rather than crashing.
        for endpoint in (u, v):
            if endpoint not in dsu.parent:
                dsu.parent[endpoint] = endpoint
                dsu.rank[endpoint] = 0
                num_components_remaining += 1

        if dsu.union(u, v):
            total_cost += w
            selected_edge_ids.append(edge_id)
            num_components_remaining -= 1
        # else: cycle-forming edge (including duplicate/parallel edges
        # and duplicated-weight ties already resolved by an earlier,
        # lower-ID edge) -> skipped, as required.

    return total_cost, selected_edge_ids


# ============================================================
# TESTS
# ============================================================
class TestMinimumSpanningForest(unittest.TestCase):

    def test_original_demo_case(self):
        # Preserves the original example and its tie-breaking outcome.
        vertices = [0, 1, 2, 3, 4, 5]
        edges = [
            (0, 1, 4),   # id 0
            (1, 2, 4),   # id 1  tie with id0's weight
            (2, 3, 1),   # id 2
            (0, 3, 5),   # id 3
            (0, 2, 2),   # id 4
            (4, 5, 3),   # id 5
            (1, 3, 4),   # id 6  another tie at weight 4
            (2, 2, 100), # id 7  self-loop
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        self.assertEqual(total_cost, 10)
        self.assertEqual(selected, [2, 4, 5, 0])

    # --- Boundary case 1: empty graph ---
    def test_empty_graph(self):
        total_cost, selected = minimum_spanning_forest([], [])
        self.assertEqual(total_cost, 0)
        self.assertEqual(selected, [])

    # --- Boundary case 2: single vertex, no edges ---
    def test_single_vertex_no_edges(self):
        total_cost, selected = minimum_spanning_forest([42], [])
        self.assertEqual(total_cost, 0)
        self.assertEqual(selected, [])

    # --- Boundary case 3: multiple isolated vertices, zero edges ---
    def test_all_isolated_vertices(self):
        total_cost, selected = minimum_spanning_forest([1, 2, 3, 4], [])
        self.assertEqual(total_cost, 0)
        self.assertEqual(selected, [])

    # --- Boundary case 4: only self-loops present ---
    def test_only_self_loops(self):
        vertices = [1, 2, 3]
        edges = [
            (1, 1, 5),   # id 0
            (2, 2, -3),  # id 1
            (3, 3, 0),   # id 2
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        self.assertEqual(total_cost, 0)
        self.assertEqual(selected, [])

    # --- Boundary case 5: duplicate / parallel edges, some tied weight ---
    def test_duplicate_parallel_edges(self):
        vertices = [1, 2]
        edges = [
            (1, 2, 7),  # id 0
            (1, 2, 7),  # id 1  tie -> lower id (0) already used first
            (1, 2, 3),  # id 2  actually cheaper, should win instead
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        # Sorted by (weight, id): (3,id2),(7,id0),(7,id1)
        # id2 chosen first (cheapest), then id0/id1 form cycles.
        self.assertEqual(total_cost, 3)
        self.assertEqual(selected, [2])

    # --- Boundary case 6: all edges share identical weight ---
    def test_all_equal_weights_tie_break_by_id(self):
        vertices = [1, 2, 3, 4]
        edges = [
            (1, 2, 10),  # id 0
            (2, 3, 10),  # id 1
            (3, 4, 10),  # id 2
            (1, 4, 10),  # id 3 (would form a cycle after first 3)
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        # All weights equal -> pure ascending ID order: 0,1,2 connect
        # everything; id3 forms a cycle and is skipped.
        self.assertEqual(total_cost, 30)
        self.assertEqual(selected, [0, 1, 2])

    # --- Boundary case 7: negative, zero, and float weights mixed ---
    def test_negative_zero_and_float_weights(self):
        vertices = ["a", "b", "c"]
        edges = [
            ("a", "b", -5.5),  # id 0
            ("b", "c", 0),     # id 1
            ("a", "c", 2.25),  # id 2 (would create a cycle)
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        self.assertAlmostEqual(total_cost, -5.5)
        self.assertEqual(selected, [0, 1])

    # --- Boundary case 8: disconnected graph -> real forest, multiple trees
    def test_disconnected_components(self):
        vertices = [1, 2, 3, 4, 5, 6, 7]
        edges = [
            (1, 2, 1),  # id 0  component A
            (2, 3, 2),  # id 1  component A
            (4, 5, 1),  # id 2  component B
            (6, 7, 9),  # id 3  component C
            # vertex isolated: none extra here, 7 is used
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        self.assertEqual(total_cost, 1 + 2 + 1 + 9)
        self.assertEqual(selected, [0, 1, 2, 3])

    # --- Boundary case 9: large / sparse / non-contiguous vertex & ID space
    def test_large_sparse_ids(self):
        vertices = [1000000, 2000000, 3000000]
        edges = [
            (1000000, 3000000, 50),  # id 0
            (1000000, 2000000, 10),  # id 1
            (2000000, 3000000, 10),  # id 2 tie with id1, but forms cycle
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        # Sorted by (weight, id): (10,id1),(10,id2),(50,id0)
        # id1 connects 1000000-2000000; id2 connects the rest cheaper
        # than id0's 50, so id0 never needed.
        self.assertEqual(total_cost, 20)
        self.assertEqual(selected, [1, 2])

    # --- Boundary case 10: many duplicated equal-weight edges on one pair
    def test_many_duplicates_same_pair_same_weight(self):
        vertices = [1, 2]
        edges = [(1, 2, 5) for _ in range(10)]  # ids 0..9, all identical
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        # Only the lowest-ID edge (id 0) is ever selected.
        self.assertEqual(total_cost, 5)
        self.assertEqual(selected, [0])

    # --- Boundary case 11: edge references a vertex not in `vertices` ---
    def test_edge_with_unlisted_vertex_is_tolerated(self):
        vertices = [1, 2]
        edges = [
            (1, 2, 3),  # id 0
            (2, 99, 1), # id 1 -> 99 not declared in `vertices`
        ]
        total_cost, selected = minimum_spanning_forest(vertices, edges)
        # Sorted by weight: (1,id1) first, then (3,id0)
        self.assertEqual(total_cost, 4)
        self.assertEqual(selected, [1, 0])


if __name__ == "__main__":
    unittest.main(verbosity=2)