import heapq

def dijkstra(num_vertices: int, edges: list[tuple[int, int, int]], source: int) -> list[int]:
    """
    Computes shortest distances from source to all vertices using Dijkstra's Algorithm.

    :param num_vertices: Total number of vertices (0 to num_vertices - 1).
    :param edges: List of tuples (u, v, w) representing a directed edge u -> v with weight w.
    :param source: The source vertex index.
    :return: List of shortest path distances, with -1 for unreachable vertices.
    """
    # Build adjacency list: graph[u] = list of (v, weight)
    graph = [[] for _ in range(num_vertices)]
    for u, v, w in edges:
        graph[u].append((v, w))

    # Initialize distances with infinity
    distances = [float('inf')] * num_vertices
    distances[source] = 0

    # Priority queue stores tuples of (distance, vertex)
    min_heap = [(0, source)]

    while min_heap:
        current_dist, u = heapq.heappop(min_heap)

        # Skip stale entries
        if current_dist > distances[u]:
            continue

        for v, weight in graph[u]:
            distance = current_dist + weight

            # Relaxation step
            if distance < distances[v]:
                distances[v] = distance
                heapq.heappush(min_heap, (distance, v))

    # Convert unreachable distances (inf) to -1
    return [d if d != float('inf') else -1 for d in distances]


# --- Example Usage ---
if __name__ == "__main__":
    V = 5
    # Edges defined as (u, v, weight)
    edges = [
        (0, 1, 4),
        (0, 2, 2),
        (1, 2, 1),
        (1, 3, 5),
        (2, 3, 8),
        (2, 4, 10),
        (3, 4, 2)
    ]
    source = 0

    result = dijkstra(V, edges, source)
    print("Shortest distances from source:", result)
    # Expected output: [0, 4, 2, 9, 11]