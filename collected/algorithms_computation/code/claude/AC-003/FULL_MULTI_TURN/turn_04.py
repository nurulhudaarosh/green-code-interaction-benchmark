"""
Single-Source Route Analyzer
Shortest paths on a directed, non-negatively weighted graph using
Dijkstra's algorithm with a binary heap (heapq), with deterministic
tie-breaking via an explicit insertion-order counter.

Unreachable vertices are reported with distance -1.

Optional feature: when include_operation_summary=True, also returns a
deterministic count of major computational decisions/operations made
by the algorithm. When disabled (default), the return value is exactly
the original {vertex: distance} mapping, unchanged.

Standard library only. No randomness, no network access, fully deterministic.
Includes boundary-case unit tests (run this file directly).
"""

import heapq
import itertools
import unittest
from collections import defaultdict
from typing import Dict, Hashable, Iterable, List, Tuple, Union


class Graph:
    """A directed graph represented as an adjacency list."""

    def __init__(self) -> None:
        self._adj: Dict[Hashable, List[Tuple[Hashable, float]]] = defaultdict(list)
        self._vertices: set = set()

    def add_vertex(self, v: Hashable) -> None:
        self._vertices.add(v)
        _ = self._adj[v]  # ensure it appears even with no outgoing edges

    def add_edge(self, u: Hashable, v: Hashable, weight: float) -> None:
        if weight < 0:
            raise ValueError(
                f"Edge ({u!r} -> {v!r}) has negative weight {weight!r}; "
                "Dijkstra's algorithm requires non-negative weights."
            )
        self.add_vertex(u)
        self.add_vertex(v)
        self._adj[u].append((v, weight))

    def vertices(self) -> Iterable[Hashable]:
        return self._vertices

    def neighbors(self, v: Hashable) -> List[Tuple[Hashable, float]]:
        return self._adj.get(v, [])


def dijkstra(
    graph: Graph,
    source: Hashable,
    include_operation_summary: bool = False,
) -> Union[Dict[Hashable, int], Dict[str, dict]]:
    """
    Compute shortest distances from `source` to every vertex in `graph`.

    Default behavior (include_operation_summary=False):
        Returns vertex -> distance, with -1 for unreachable vertices.

    Extended behavior (include_operation_summary=True):
        Returns {"distances": {...}, "operation_summary": {...}}.

    Deterministic tie-breaking: heap entries are (distance, insertion_order,
    vertex), so heapq never compares vertex labels against each other.
    Parallel edges are naturally handled: relaxation only accepts an edge
    if it strictly improves the current best distance, so the minimum-
    weight parallel edge always wins regardless of insertion order.
    """
    if source not in graph.vertices():
        raise ValueError(f"Source vertex {source!r} is not in the graph.")

    INF = float("inf")
    dist: Dict[Hashable, float] = {v: INF for v in graph.vertices()}
    dist[source] = 0

    counter = itertools.count()
    heap: List[Tuple[float, int, Hashable]] = [(0, next(counter), source)]
    visited: set = set()

    vertices_finalized = 0
    edges_relaxed_attempted = 0
    edges_relaxed_successful = 0
    heap_pushes = 1
    stale_pops_skipped = 0

    while heap:
        d, _, u = heapq.heappop(heap)

        if u in visited:
            stale_pops_skipped += 1
            continue
        visited.add(u)
        vertices_finalized += 1

        for v, w in graph.neighbors(u):
            edges_relaxed_attempted += 1
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, next(counter), v))
                edges_relaxed_successful += 1
                heap_pushes += 1

    distances: Dict[Hashable, int] = {}
    for v, d in dist.items():
        if d == INF:
            distances[v] = -1
        else:
            distances[v] = int(d) if float(d).is_integer() else d

    if not include_operation_summary:
        return distances

    operation_summary = {
        "vertices_finalized": vertices_finalized,
        "edges_relaxed_attempted": edges_relaxed_attempted,
        "edges_relaxed_successful": edges_relaxed_successful,
        "heap_pushes": heap_pushes,
        "stale_pops_skipped": stale_pops_skipped,
    }
    return {"distances": distances, "operation_summary": operation_summary}


def build_graph(edges: Iterable[Tuple[Hashable, Hashable, float]],
                 vertices: Iterable[Hashable] = ()) -> Graph:
    """Convenience constructor from an edge list plus optional isolated vertices."""
    g = Graph()
    for v in vertices:
        g.add_vertex(v)
    for u, v, w in edges:
        g.add_edge(u, v, w)
    return g


# --------------------------------------------------------------------------
# Boundary-case tests
# --------------------------------------------------------------------------

class TestBoundaryCases(unittest.TestCase):

    def test_single_vertex_no_edges(self):
        """Boundary: graph with exactly one vertex (the source), no edges."""
        g = Graph()
        g.add_vertex("A")
        self.assertEqual(dijkstra(g, "A"), {"A": 0})

    def test_self_loop_on_source(self):
        """Boundary: source has a self-loop; must not corrupt its own distance."""
        g = build_graph([("A", "A", 5), ("A", "B", 2)])
        self.assertEqual(dijkstra(g, "A"), {"A": 0, "B": 2})

    def test_zero_weight_edges(self):
        """Boundary: minimum valid edge weight (0) must be accepted and used."""
        g = build_graph([("A", "B", 0), ("B", "C", 0), ("A", "C", 10)])
        self.assertEqual(dijkstra(g, "A"), {"A": 0, "B": 0, "C": 0})

    def test_negative_weight_rejected(self):
        """Boundary: just below the valid range (0) must raise immediately."""
        g = Graph()
        with self.assertRaises(ValueError):
            g.add_edge("A", "B", -1)

    def test_parallel_edges_min_selected(self):
        """Boundary: duplicate edges between same pair; minimum must win,
        regardless of insertion order."""
        g = build_graph([("A", "B", 10), ("A", "B", 3), ("A", "B", 7)])
        self.assertEqual(dijkstra(g, "A"), {"A": 0, "B": 3})

    def test_fully_disconnected_graph(self):
        """Boundary: no vertex other than source is reachable."""
        g = Graph()
        g.add_vertex("A")
        g.add_vertex("B")
        g.add_vertex("C")
        self.assertEqual(dijkstra(g, "A"), {"A": 0, "B": -1, "C": -1})

    def test_source_not_in_graph_raises(self):
        """Boundary: source absent from the graph entirely -> explicit error."""
        g = build_graph([("X", "Y", 1)])
        with self.assertRaises(ValueError):
            dijkstra(g, "NOT_PRESENT")

    def test_large_weight_values(self):
        """Boundary: very large finite weights combine correctly."""
        big = 10**15
        g = build_graph([("A", "B", big), ("B", "C", big)])
        self.assertEqual(dijkstra(g, "A"), {"A": 0, "B": big, "C": 2 * big})

    def test_deterministic_repeated_runs_larger_graph(self):
        """Boundary/scale: repeated runs on a larger graph with many ties
        produce identical output every time (determinism holds at scale)."""
        edges = []
        n = 200
        for i in range(n):
            edges.append(("S", f"V{i}", 1))  # all tied at distance 1 from S
        g = build_graph(edges)

        first = dijkstra(g, "S")
        for _ in range(5):
            self.assertEqual(dijkstra(g, "S"), first)

    def test_operation_summary_unaffected_shape_when_disabled(self):
        """Boundary: feature flag off preserves the original plain-dict shape
        even in edge-case graphs (single vertex)."""
        g = Graph()
        g.add_vertex("A")
        result = dijkstra(g, "A", include_operation_summary=False)
        self.assertEqual(result, {"A": 0})
        self.assertNotIn("operation_summary", result)


def _demo() -> None:
    """Deterministic self-contained demonstration of both modes."""
    edges = [
        ("A", "B", 4),
        ("A", "C", 1),
        ("C", "B", 2),
        ("B", "D", 5),
        ("C", "D", 8),
        ("D", "E", 3),
        ("G", "F", 1),
        ("A", ("x", 1), 3),
    ]
    g = build_graph(edges, vertices=["F"])
    source = "A"

    print("-- Default mode --")
    distances = dijkstra(g, source)
    for v in sorted(distances.keys(), key=str):
        print(f"  {v}: {distances[v]}")

    print("\n-- Extended mode (include_operation_summary=True) --")
    result = dijkstra(g, source, include_operation_summary=True)
    for v in sorted(result["distances"].keys(), key=str):
        print(f"  {v}: {result['distances'][v]}")
    print("  operation_summary:", result["operation_summary"])


if __name__ == "__main__":
    _demo()
    print("\n-- Running boundary-case tests --")
    unittest.main(argv=[""], exit=False, verbosity=2)