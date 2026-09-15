"""
Single-Source Route Analyzer
Shortest paths on a directed, non-negatively weighted graph using
Dijkstra's algorithm with a binary heap (heapq), with deterministic
tie-breaking via an explicit insertion-order counter.

Unreachable vertices are reported with distance -1.
Standard library only. No randomness, no network access, fully deterministic.
"""

import heapq
import itertools
from collections import defaultdict
from typing import Dict, Hashable, Iterable, List, Tuple


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


def dijkstra(graph: Graph, source: Hashable) -> Dict[Hashable, int]:
    """
    Compute shortest distances from `source` to every vertex in `graph`.
    Returns vertex -> distance, with -1 for unreachable vertices.

    Deterministic tie-breaking: heap entries are (distance, insertion_order,
    vertex). The insertion_order counter is strictly increasing and unique,
    so heapq never needs to compare vertex labels against each other,
    eliminating both TypeErrors on incomparable labels and any dependence
    on accidental label ordering.
    """
    if source not in graph.vertices():
        raise ValueError(f"Source vertex {source!r} is not in the graph.")

    INF = float("inf")
    dist: Dict[Hashable, float] = {v: INF for v in graph.vertices()}
    dist[source] = 0

    counter = itertools.count()  # deterministic, strictly increasing tie-breaker
    heap: List[Tuple[float, int, Hashable]] = [(0, next(counter), source)]
    visited: set = set()

    while heap:
        d, _, u = heapq.heappop(heap)

        if u in visited:
            continue  # stale entry: a shorter distance was already finalized
        visited.add(u)

        for v, w in graph.neighbors(u):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, next(counter), v))

    result: Dict[Hashable, int] = {}
    for v, d in dist.items():
        if d == INF:
            result[v] = -1
        else:
            result[v] = int(d) if float(d).is_integer() else d
    return result


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
    """Deterministic self-contained demonstration, including a tie case with
    mixed, mutually-incomparable vertex labels that previously crashed."""
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
    distances = dijkstra(g, source)

    print(f"Shortest distances from source '{source}':")
    for v in sorted(distances.keys(), key=str):
        print(f"  {v}: {distances[v]}")


if __name__ == "__main__":
    _demo()