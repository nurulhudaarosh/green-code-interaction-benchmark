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
"""

import heapq
import itertools
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
        Identical in shape and content to the original implementation.

    Extended behavior (include_operation_summary=True):
        Returns:
            {
              "distances": {vertex -> distance, ... same as default ...},
              "operation_summary": {
                  "vertices_finalized": int,
                  "edges_relaxed_attempted": int,
                  "edges_relaxed_successful": int,
                  "heap_pushes": int,
                  "stale_pops_skipped": int,
              }
            }

    Deterministic tie-breaking: heap entries are (distance, insertion_order,
    vertex), so heapq never compares vertex labels against each other.
    """
    if source not in graph.vertices():
        raise ValueError(f"Source vertex {source!r} is not in the graph.")

    INF = float("inf")
    dist: Dict[Hashable, float] = {v: INF for v in graph.vertices()}
    dist[source] = 0

    counter = itertools.count()  # deterministic, strictly increasing tie-breaker
    heap: List[Tuple[float, int, Hashable]] = [(0, next(counter), source)]
    visited: set = set()

    # Operation counters (major computational decisions made by the algorithm).
    vertices_finalized = 0
    edges_relaxed_attempted = 0
    edges_relaxed_successful = 0
    heap_pushes = 1  # the initial source push counts as an operation
    stale_pops_skipped = 0

    while heap:
        d, _, u = heapq.heappop(heap)

        if u in visited:
            stale_pops_skipped += 1
            continue  # stale entry: a shorter distance was already finalized
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
        return distances  # unchanged original output shape

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


def _demo() -> None:
    """Deterministic self-contained demonstration of both modes."""
    edges = [
        ("A", "B", 4),
        ("A", "C", 1),
        ("C", "B", 2),
        ("B", "D", 5),
        ("C", "D", 8),
        ("D", "E", 3),
        ("G", "F", 1),      # F/G unreachable from A
        ("A", ("x", 1), 3),  # tuple-labeled vertex tied at distance 3 with "B"
    ]
    g = build_graph(edges, vertices=["F"])
    source = "A"

    print("-- Default mode (feature disabled; unchanged original output) --")
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