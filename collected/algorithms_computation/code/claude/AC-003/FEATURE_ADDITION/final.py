"""
PROBLEM (restated)
-------------------
Single-Source Route Analyzer: Given a directed graph with non-negative edge
weights and a source vertex, compute the shortest distance from the source
to every vertex, using -1 for unreachable vertices.

CONSTRAINTS
-----------
1. The graph is directed.
2. Edge weights are non-negative (w >= 0), required for Dijkstra correctness.
3. Vertices are identified by integers 0..V-1 (V = number of vertices).
4. The graph may be disconnected; unreachable vertices get distance -1.
5. Deterministic: no randomness, no network access, no external services,
   no human interaction — standard library only.

REQUIRED OUTPUT (original, unchanged)
--------------------------------------
A list/array `dist` of length V such that:
    dist[v] = shortest distance from source to v, if reachable
    dist[v] = -1, if v is unreachable
    dist[source] = 0

NEW FEATURE (additive, opt-in)
-------------------------------
When explicitly requested, the solution also returns an `operation_summary`
field: a deterministic count of the major computational decisions/operations
Dijkstra's algorithm performed, specifically:
    - "pops":            number of heap pop operations (vertices dequeued)
    - "stale_skips":     number of pops skipped as stale (outdated) entries
    - "edges_examined":  number of edges relaxed/checked
    - "relaxations":     number of successful relaxations (distance updates)
    - "pushes":          number of heap push operations

When the feature is disabled or not requested, behavior, signature, and
output are identical to the original: only `dist` is returned, nothing else
changes.

ALGORITHM
---------
Dijkstra's algorithm using an adjacency list and a binary min-heap
(heapq): initialize distances to infinity except the source (0); repeatedly
pop the minimum-distance vertex, skip stale heap entries, relax outgoing
edges, and push improved distances. Convert leftover infinities to -1.
Time complexity: O((V + E) log V).
"""

import heapq
from typing import List, Tuple, Dict, Union


def build_adjacency_list(num_vertices: int,
                          edges: List[Tuple[int, int, int]]) -> List[List[Tuple[int, int]]]:
    """
    Build a directed adjacency list from a list of edges.
    edges: list of (u, v, w) meaning a directed edge u -> v with weight w.
    Returns adj where adj[u] = list of (v, w).
    """
    adj: List[List[Tuple[int, int]]] = [[] for _ in range(num_vertices)]
    for u, v, w in edges:
        if w < 0:
            raise ValueError(f"Edge ({u}, {v}) has negative weight {w}; "
                              "Dijkstra's algorithm requires non-negative weights.")
        adj[u].append((v, w))
    return adj


def dijkstra(num_vertices: int,
             adj: List[List[Tuple[int, int]]],
             source: int,
             with_summary: bool = False
             ) -> Union[List[int], Tuple[List[int], Dict[str, int]]]:
    """
    Compute shortest distances from `source` to all vertices using
    Dijkstra's algorithm with a binary heap.

    If with_summary is False (default): returns dist (original behavior,
    unchanged).

    If with_summary is True: returns (dist, operation_summary), where
    operation_summary is a dict of deterministic operation counts.
    """
    if not (0 <= source < num_vertices):
        raise ValueError(f"source {source} is out of range [0, {num_vertices - 1}]")

    INF = float('inf')
    dist = [INF] * num_vertices
    dist[source] = 0

    heap: List[Tuple[int, int]] = [(0, source)]

    # Operation counters (only used/returned when with_summary=True)
    pops = 0
    stale_skips = 0
    edges_examined = 0
    relaxations = 0
    pushes = 1  # initial push of (0, source)

    while heap:
        d_u, u = heapq.heappop(heap)
        pops += 1

        if d_u > dist[u]:
            stale_skips += 1
            continue

        for v, w in adj[u]:
            edges_examined += 1
            new_dist = d_u + w
            if new_dist < dist[v]:
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))
                relaxations += 1
                pushes += 1

    final_dist = [d if d != INF else -1 for d in dist]

    if not with_summary:
        return final_dist

    operation_summary = {
        "pops": pops,
        "stale_skips": stale_skips,
        "edges_examined": edges_examined,
        "relaxations": relaxations,
        "pushes": pushes,
        "total_major_operations": pops + edges_examined + pushes,
    }
    return final_dist, operation_summary


def shortest_distances(num_vertices: int,
                        edges: List[Tuple[int, int, int]],
                        source: int,
                        with_summary: bool = False
                        ) -> Union[List[int], Tuple[List[int], Dict[str, int]]]:
    """
    Convenience wrapper: builds the adjacency list and runs Dijkstra.

    num_vertices: number of vertices, labeled 0..num_vertices-1
    edges: list of (u, v, w) directed edges with non-negative weight w
    source: the source vertex
    with_summary: if False (default), returns dist only (original,
                  unchanged behavior). If True, returns (dist, operation_summary).
    """
    adj = build_adjacency_list(num_vertices, edges)
    return dijkstra(num_vertices, adj, source, with_summary=with_summary)


if __name__ == "__main__":
    num_vertices = 7
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (3, 4, 3),
        (5, 0, 10),
    ]
    source = 0

    # --- Original behavior: unchanged, dist only ---
    result = shortest_distances(num_vertices, edges, source)
    print("Original mode (no summary) - distances from source", source)
    for vertex, d in enumerate(result):
        print(f"  vertex {vertex}: {d}")

    expected = [0, 3, 1, 4, 7, -1, -1]
    assert result == expected, f"Self-test failed: got {result}, expected {expected}"
    print("Self-test (original mode) passed.\n")

    # --- New feature: with operation_summary ---
    result_with_summary, operation_summary = shortest_distances(
        num_vertices, edges, source, with_summary=True
    )
    print("Extended mode (with summary) - distances from source", source)
    for vertex, d in enumerate(result_with_summary):
        print(f"  vertex {vertex}: {d}")

    print("\noperation_summary:")
    for key, value in operation_summary.items():
        print(f"  {key}: {value}")

    assert result_with_summary == expected, "Self-test failed: dist mismatch in summary mode"
    assert isinstance(operation_summary, dict)
    assert all(isinstance(v, int) and v >= 0 for v in operation_summary.values())
    print("\nSelf-test (extended mode) passed.")