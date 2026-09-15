from heapq import heappush, heappop


def shortest_distances(n, edges, source):
    """
    Compute shortest distances from source to every vertex in a
    directed graph with non-negative edge weights.

    Parameters:
        n      : Number of vertices, labeled 0 through n-1.
        edges  : Iterable of (u, v, weight) directed edges.
        source : Starting vertex.

    Returns:
        A list of length n where:
        - result[v] is the shortest distance from source to v.
        - result[v] is -1 if v is unreachable.
    """

    # Build adjacency list.
    graph = [[] for _ in range(n)]

    for u, v, weight in edges:
        graph[u].append((v, weight))

    # Sort adjacency lists to make processing deterministic
    # even if the input edge order differs.
    for neighbors in graph:
        neighbors.sort(key=lambda x: (x[0], x[1]))

    # Infinity represents an initially unknown distance.
    INF = float("inf")
    dist = [INF] * n
    dist[source] = 0

    # Binary heap containing (distance, vertex).
    # The vertex ID provides deterministic tie handling.
    heap = [(0, source)]

    while heap:
        current_dist, u = heappop(heap)

        # Ignore stale heap entries.
        if current_dist != dist[u]:
            continue

        # Relax outgoing edges.
        for v, weight in graph[u]:
            new_dist = current_dist + weight

            if new_dist < dist[v]:
                dist[v] = new_dist
                heappush(heap, (new_dist, v))

    # Convert unreachable vertices from infinity to -1.
    return [-1 if d == INF else d for d in dist]


if __name__ == "__main__":
    # Example:
    #
    # 0 -> 1 (4)
    # 0 -> 2 (1)
    # 2 -> 1 (2)
    # 1 -> 3 (1)
    # 2 -> 3 (5)
    #
    # Shortest distances from 0:
    # 0, 3, 1, 4
    #
    # Vertex 4 is disconnected, so its distance is -1.

    n = 5
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
    ]
    source = 0

    result = shortest_distances(n, edges, source)
    print(result)