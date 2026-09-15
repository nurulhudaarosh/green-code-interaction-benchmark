import heapq
from typing import Dict, List, Tuple


def dijkstra(
    num_vertices: int,
    adj_list: Dict[int, List[Tuple[int, int]]],
    source: int
) -> List[int]:
    """
    Computes the shortest path from a source vertex to all vertices.
    
    :param num_vertices: Total number of vertices (0 to num_vertices - 1).
    :param adj_list: Adjacency list where adj_list[u] contains tuples (v, weight).
    :param source: The starting vertex index.
    :return: List of shortest distances where index i is the distance to vertex i (-1 if unreachable).
    """
    # Distance initialization
    distances = [float('inf')] * num_vertices
    distances[source] = 0
    
    # Priority Queue stores tuples of (distance, vertex)
    min_heap = [(0, source)]
    
    while min_heap:
        current_dist, u = heapq.heappop(min_heap)
        
        # Skip stale heap entries
        if current_dist > distances[u]:
            continue
            
        # Relax edges
        for neighbor, weight in adj_list.get(u, []):
            distance_via_u = current_dist + weight
            
            if distance_via_u < distances[neighbor]:
                distances[neighbor] = distance_via_u
                heapq.heappush(min_heap, (distance_via_u, neighbor))
                
    # Format unreachable vertices as -1
    return [int(d) if d != float('inf') else -1 for d in distances]


# Example Usage
if __name__ == "__main__":
    n = 5
    # Adjacency list: u -> [(v1, w1), (v2, w2), ...]
    graph = {
        0: [(1, 4), (2, 1)],
        1: [(3, 1)],
        2: [(1, 2), (3, 5)],
        3: [],
        4: []  # Unreachable vertex
    }
    src = 0
    
    result = dijkstra(n, graph, src)
    print(f"Shortest distances from source {src}: {result}")
    # Expected output: [0, 3, 1, 4, -1]