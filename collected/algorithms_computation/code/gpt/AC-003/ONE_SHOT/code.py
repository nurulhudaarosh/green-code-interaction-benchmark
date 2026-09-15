from heapq import heappush, heappop


def dijkstra(n, edges, source):
    """
    Compute shortest distances from source in a directed graph.

    Parameters:
        n      : number of vertices, labeled 0 to n-1
        edges  : list of (u, v, weight) directed edges
        source : source vertex

    Returns:
        A list of length n containing the shortest distance from source
        to every vertex, or -1 for unreachable vertices.
    """

    # Build adjacency list.
    graph = [[] for _ in range(n)]

    for u, v, weight in edges:
        graph[u].append((v, weight))

    # Distance array.
    INF = float("inf")
    dist = [INF] * n
    dist[source] = 0

    # Binary min-heap: (distance, vertex)
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

    # Convert unreachable distances to -1.
    return [-1 if d == INF else d for d in dist]


def main():
    # Example:
    #
    # 0 -> 1 (4)
    # 0 -> 2 (1)
    # 2 -> 1 (2)
    # 1 -> 3 (1)
    # 2 -> 3 (5)
    #
    # Shortest distances from 0:
    # 0 = 0
    # 1 = 3
    # 2 = 1
    # 3 = 4

    n = 4
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
    ]
    source = 0

    result = dijkstra(n, edges, source)
    print(result)


if __name__ == "__main__":
    main()