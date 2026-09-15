import heapq
from typing import List, Tuple, Dict

def single_source_route_analyzer(
    num_vertices: int, 
    edges: List[Tuple[int, int, int]], 
    source: int
) -> List[int]:
    """
    Computes shortest distances from a single source to all vertices deterministically.
    
    :param num_vertices: Total number of vertices (0 to num_vertices - 1)
    :param edges: List of directed edges as (u, v, weight)
    :param source: Starting vertex ID
    :return: List of shortest path distances (-1 for unreachable nodes)
    """
    # 1. Build and sort adjacency lists deterministically
    # Primary sort by target vertex v, secondary by weight w
    graph: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(num_vertices)}
    for u, v, w in edges:
        graph[u].append((v, w))
        
    for u in graph:
        graph[u].sort(key=lambda edge: (edge[0], edge[1]))

    # 2. Distance tracking
    distances = [float('inf')] * num_vertices
    distances[source] = 0

    # 3. Min-heap with deterministic tuple comparison (distance, vertex)
    min_heap: List[Tuple[int, int]] = [(0, source)]

    while min_heap:
        current_dist, u = heapq.heappop(min_heap)

        # Lazy deletion of outdated heap entries
        if current_dist > distances[u]:
            continue

        # Explore neighbors in sorted order
        for v, weight in graph[u]:
            new_dist = current_dist + weight

            # Strict comparison ensures deterministic tie-breaking & minimal heap pushes
            if new_dist < distances[v]:
                distances[v] = new_dist
                heapq.heappush(min_heap, (new_dist, v))

    # Convert unreachable nodes to -1
    return [int(d) if d != float('inf') else -1 for d in distances]


# --- Verification Example ---
if __name__ == "__main__":
    n = 4
    # Identical structure, different input ordering
    edges_a = [(0, 1, 5), (0, 2, 5), (2, 3, 2), (1, 3, 2)]
    edges_b = [(0, 2, 5), (0, 1, 5), (1, 3, 2), (2, 3, 2)]

    res_a = single_source_route_analyzer(n, edges_a, 0)
    res_b = single_source_route_analyzer(n, edges_b, 0)

    assert res_a == res_b == [0, 5, 5, 7]
    print("Deterministic Result:", res_a)