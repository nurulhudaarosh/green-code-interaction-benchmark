import heapq
from typing import Dict, List, Tuple

def analyze_routes(
    num_vertices: int,
    adj_list: Dict[int, List[Tuple[int, int]]],
    source: int
) -> List[int]:
    """
    Computes shortest path distances using Dijkstra's algorithm with deterministic
    insertion-order tie handling via a monotonic sequence counter.
    
    :param num_vertices: Total number of vertices in the graph.
    :param adj_list: Mapping of vertex -> list of (neighbor, weight) tuples.
    :param source: Starting vertex index.
    :return: List of shortest distances (-1 for unreachable vertices).
    """
    distances = [float('inf')] * num_vertices
    distances[source] = 0
    
    # Monotonic counter ensures deterministic FIFO tie-handling when distances are equal
    counter = 0
    
    # Priority Queue stores tuples: (distance, insertion_order, vertex)
    min_heap = [(0, counter, source)]
    
    while min_heap:
        current_dist, _, u = heapq.heappop(min_heap)
        
        # Skip stale entries
        if current_dist > distances[u]:
            continue
            
        # Process outgoing edges in deterministic order
        # (sorting neighbors by vertex ID ensures stable relaxation sequence)
        neighbors = sorted(adj_list.get(u, []), key=lambda x: x[0])
        
        for neighbor, weight in neighbors:
            distance_via_u = current_dist + weight
            
            if distance_via_u < distances[neighbor]:
                distances[neighbor] = distance_via_u
                counter += 1
                heapq.heappush(min_heap, (distance_via_u, counter, neighbor))
                
    return [int(d) if d != float('inf') else -1 for d in distances]


if __name__ == "__main__":
    n = 4
    # Both node 1 and node 2 are at distance 2 from node 0
    graph = {
        0: [(1, 2), (2, 2)],
        1: [(3, 1)],
        2: [(3, 1)],
        3: []
    }
    
    result = analyze_routes(n, graph, 0)
    print("Deterministically calculated distances:", result)
    # Output: [0, 2, 2, 3]