from heapq import heappush, heappop
from typing import List, Tuple


def single_source_route_analyzer(
    n: int,
    edges: List[Tuple[int, int, int]],
    source: int
) -> List[int]:
    """
    Compute shortest distances from source to every vertex
    in a directed graph with non-negative edge weights.

    Args:
        n: Number of vertices, numbered 0 to n - 1.
        edges: List of (u, v, weight) directed edges.
        source: Source vertex.

    Returns:
        A list where result[v] is the shortest distance from
        source to v, or -1 if v is unreachable.
    """

    # Build adjacency list.
    adj = [[] for _ in range(n)]

    for u, v, weight in edges:
        if weight < 0:
            raise ValueError("Dijkstra's algorithm requires non-negative weights.")
        adj[u].append((v, weight))

    # Initialize distances.
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

        # Relax all outgoing edges.
        for v, weight in adj[u]:
            new_dist = current_dist + weight

            if new_dist < dist[v]:
                dist[v] = new_dist
                heappush(heap, (new_dist, v))

    # Replace unreachable distances with -1.
    return [-1 if d == INF else int(d) for d in dist]


# Example
if __name__ == "__main__":
    n = 5
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
    ]
    source = 0

    print(single_source_route_analyzer(n, edges, source))
    # Output: [0, 3, 1, 4, -1]