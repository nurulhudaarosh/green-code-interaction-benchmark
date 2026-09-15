import heapq
import math
from collections import defaultdict


def build_adjacency_list(n, edges):
    """
    Build an adjacency list from a list of directed edges.

    n: number of vertices (0-indexed: 0 .. n-1)
    edges: list of (u, v, weight) tuples representing directed edges u -> v
    """
    adj = defaultdict(list)
    for u, v, w in edges:
        if w < 0:
            raise ValueError(f"Edge ({u}, {v}) has negative weight {w}; "
                              f"Dijkstra's algorithm requires non-negative weights.")
        adj[u].append((v, w))
    # Ensure every vertex has an entry (even if it has no outgoing edges)
    for i in range(n):
        adj.setdefault(i, [])
    return adj


def dijkstra(n, edges, source):
    """
    Compute shortest distances from `source` to every vertex in a directed
    graph with non-negative edge weights, using Dijkstra's algorithm with
    a binary heap.

    n: number of vertices (0-indexed: 0 .. n-1)
    edges: list of (u, v, weight) tuples
    source: the source vertex index

    Returns: list `dist` of length n, where dist[i] is the shortest distance
             from source to i, or -1 if i is unreachable.
    """
    if not (0 <= source < n):
        raise ValueError(f"Source vertex {source} is out of range [0, {n - 1}].")

    adj = build_adjacency_list(n, edges)

    dist = [math.inf] * n
    dist[source] = 0

    # Min-heap of (distance, vertex)
    heap = [(0, source)]
    visited = [False] * n

    while heap:
        d, u = heapq.heappop(heap)

        if visited[u]:
            continue  # stale entry, already finalized with a better distance
        visited[u] = True

        for v, w in adj[u]:
            if visited[v]:
                continue
            new_dist = d + w
            if new_dist < dist[v]:
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    # Replace unreachable (infinity) distances with -1
    return [d if d != math.inf else -1 for d in dist]


def main():
    # Deterministic example graph (no randomness, no external input required).
    # Vertices: 0, 1, 2, 3, 4, 5 (vertex 5 is intentionally unreachable from 0)
    n = 6
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
        (3, 4, 3),
        (4, 3, 1),
        # vertex 5 has no incoming edges -> unreachable from 0
    ]
    source = 0

    distances = dijkstra(n, edges, source)

    print(f"Shortest distances from source vertex {source}:")
    for vertex, d in enumerate(distances):
        print(f"  vertex {vertex}: {d}")


if __name__ == "__main__":
    main()