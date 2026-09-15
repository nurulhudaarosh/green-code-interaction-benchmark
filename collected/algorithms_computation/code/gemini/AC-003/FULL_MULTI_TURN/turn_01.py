import heapq
from typing import List, Tuple, Dict

def dijkstra_shortest_paths(num_vertices: int, edges: List[Tuple[int, int, int]], source: int) -> List[int]:
    """
    Computes the shortest path distance from source to all vertices using Dijkstra's algorithm.
    
    :param num_vertices: Total number of vertices (0-indexed: 0 to num_vertices - 1)
    :param edges: List of directed edges represented as (u, v, weight)
    :param source: The starting vertex index
    :return: List of shortest distances where unreachable vertices are marked with -1
    """
    # Build adjacency list: graph[u] = [(v, weight), ...]
    graph: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(num_vertices)}
    for u, v, w in edges:
        graph[u].append((v, w))

    # Initialize distances with infinity
    distances = [float('inf')] * num_vertices
    distances[source] = 0

    # Priority queue stores tuples of (distance, vertex)
    min_heap = [(0, source)]

    while min_heap:
        current_dist, u = heapq.heappop(min_heap)

        # Skip if we found a shorter path to u already
        if current_dist > distances[u]:
            continue

        # Explore neighbors
        for v, weight in graph[u]:
            distance = current_dist + weight

            # Relaxation step
            if distance < distances[v]:
                distances[v] = distance
                heapq.heappush(min_heap, (distance, v))

    # Convert unreachable vertices (float('inf')) to -1
    return [d if d != float('inf') else -1 for d in distances]


# --- Example Usage ---
if __name__ == "__main__":
    n = 5
    # Edges: (u, v, weight)
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
    ]
    src = 0

    result = dijkstra_shortest_paths(n, edges, src)
    print(f"Shortest distances from source {src}: {result}")
    # Output: [0, 3, 1, 4, -1]  (Vertex 4 is unreachable)