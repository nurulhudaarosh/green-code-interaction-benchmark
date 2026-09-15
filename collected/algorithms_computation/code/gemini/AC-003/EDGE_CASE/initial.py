import heapq

def dijkstra_shortest_paths(num_vertices: int, edges: list[tuple[int, int, int]], source: int) -> list[int]:
    """
    Computes the shortest path from source to all vertices using Dijkstra's algorithm.
    
    :param num_vertices: Total number of vertices V (indexed 0 to V-1)
    :param edges: List of tuples (u, v, weight) representing directed edges
    :param source: Starting vertex
    :return: List of shortest distances where index i is the distance to vertex i (-1 if unreachable)
    """
    # Build adjacency list: graph[u] = [(v, weight), ...]
    graph = [[] for _ in range(num_vertices)]
    for u, v, weight in edges:
        graph[u].append((v, weight))
    
    # Initialize distances with infinity
    distances = [float('inf')] * num_vertices
    distances[source] = 0
    
    # Min-priority queue storing tuples of (distance_to_u, u)
    pq = [(0, source)]
    
    while pq:
        current_dist, u = heapq.heappop(pq)
        
        # Skip stale entries in the priority queue
        if current_dist > distances[u]:
            continue
            
        # Relax edges
        for v, weight in graph[u]:
            distance_via_u = current_dist + weight
            
            if distance_via_u < distances[v]:
                distances[v] = distance_via_u
                heapq.heappush(pq, (distance_via_u, v))
    
    # Convert unreachable vertices (infinity) to -1
    return [d if d != float('inf') else -1 for d in distances]


# --- Example Usage ---
if __name__ == "__main__":
    V = 5
    # Edges: (u, v, weight)
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
    ]
    source = 0
    
    result = dijkstra_shortest_paths(V, edges, source)
    print(f"Shortest distances from source {source}: {result}")
    # Output: Shortest distances from source 0: [0, 3, 1, 4, -1]