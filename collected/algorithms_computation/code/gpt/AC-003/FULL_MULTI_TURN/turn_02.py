import heapq


def single_source_route_analyzer(n, edges, source):
    """
    Compute shortest distances from `source` to every vertex.

    Parameters:
        n: Number of vertices, numbered 0 through n-1.
        edges: Iterable of (u, v, weight) directed edges.
        source: Starting vertex.

    Returns:
        A list where result[v] is the shortest distance from source
        to v, or -1 if v is unreachable.
    """

    # Build adjacency list.
    graph = [[] for _ in range(n)]

    for u, v, weight in edges:
        graph[u].append((v, weight))

    # Sorting is not required for Dijkstra's distances, but makes
    # adjacency traversal deterministic when input ordering varies.
    for neighbors in graph:
        neighbors.sort(key=lambda item: (item[0], item[1]))

    INF = float("inf")
    dist = [INF] * n
    dist[source] = 0

    # Binary heap.
    # (distance, vertex) gives a deterministic tie-breaker.
    heap = [(0, source)]

    while heap:
        current_dist, u = heapq.heappop(heap)

        # Ignore stale heap entries.
        if current_dist != dist[u]:
            continue

        for v, weight in graph[u]:
            new_dist = current_dist + weight

            if new_dist < dist[v]:
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    return [-1 if d == INF else d for d in dist]


# Demonstration
if __name__ == "__main__":
    n = 4
    edges = [
        (0, 1, 1),
        (0, 2, 1),
        (1, 3, 1),
        (2, 3, 1),
    ]

    print(single_source_route_analyzer(n, edges, 0))