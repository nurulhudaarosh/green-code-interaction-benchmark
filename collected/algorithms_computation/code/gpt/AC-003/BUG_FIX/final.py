"""
Single-Source Route Analyzer

Problem:
Given a directed graph with non-negative edge weights and a source vertex,
compute the shortest distance from the source to every vertex.

Expected behavior:
- Vertices are numbered 0 through n-1.
- The graph is directed.
- Edge weights are non-negative.
- The source has distance 0.
- Unreachable vertices have distance -1.
- Use an adjacency list.
- Use Dijkstra's algorithm with a binary heap.
- Equal-distance heap entries are handled deterministically by vertex ID.
- Return exactly the required list of distances.

Input format:
    n m
    u v w
    u v w
    ...
    source

Output format:
    n space-separated shortest distances.

Example:
Input:
    4 4
    0 1 1
    0 2 1
    1 3 1
    2 3 1
    0

Output:
    0 1 1 2
"""

import sys
import heapq


def dijkstra(n, edges, source):
    """Compute shortest distances from source using Dijkstra's algorithm."""

    # Build adjacency list.
    graph = [[] for _ in range(n)]

    for u, v, weight in edges:
        graph[u].append((v, weight))

    # Sort neighbors so equal-distance relaxation order is deterministic.
    for neighbors in graph:
        neighbors.sort(key=lambda item: (item[0], item[1]))

    INF = float("inf")
    distances = [INF] * n
    distances[source] = 0

    # (distance, vertex)
    #
    # The vertex ID is the deterministic tie-breaker when two vertices
    # have the same tentative distance.
    heap = [(0, source)]

    while heap:
        current_distance, u = heapq.heappop(heap)

        # Ignore stale entries.
        if current_distance != distances[u]:
            continue

        for v, weight in graph[u]:
            new_distance = current_distance + weight

            if new_distance < distances[v]:
                distances[v] = new_distance
                heapq.heappush(heap, (new_distance, v))

    return [
        -1 if distance == INF else distance
        for distance in distances
    ]


def solve():
    data = sys.stdin.buffer.read().split()

    if not data:
        return

    pos = 0

    n = int(data[pos])
    pos += 1

    m = int(data[pos])
    pos += 1

    edges = []

    for _ in range(m):
        u = int(data[pos])
        v = int(data[pos + 1])
        weight = int(data[pos + 2])
        pos += 3

        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("Vertex out of range.")

        if weight < 0:
            raise ValueError("Edge weights must be non-negative.")

        edges.append((u, v, weight))

    source = int(data[pos])

    if not (0 <= source < n):
        raise ValueError("Source vertex out of range.")

    result = dijkstra(n, edges, source)

    sys.stdout.write(" ".join(map(str, result)))


if __name__ == "__main__":
    solve()