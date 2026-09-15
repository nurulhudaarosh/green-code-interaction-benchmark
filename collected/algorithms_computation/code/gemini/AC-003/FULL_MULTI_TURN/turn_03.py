import heapq
from typing import List, Tuple, Dict, Union, Any

def single_source_route_analyzer(
    num_vertices: int, 
    edges: List[Tuple[int, int, int]], 
    source: int,
    include_summary: bool = False
) -> Union[List[int], Tuple[List[int], Dict[str, int]]]:
    """
    Computes shortest distances from source to all vertices deterministically.
    Optionally returns a deterministic summary of key algorithm operations.

    :param num_vertices: Total number of vertices (0-indexed: 0 to num_vertices - 1)
    :param edges: Directed edges as (u, v, weight)
    :param source: Starting vertex ID
    :param include_summary: If True, returns (distances, operation_summary)
    :return: List of distances OR Tuple of (distances, operation_summary)
    """
    # 1. Build and sort adjacency lists for deterministic execution
    graph: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(num_vertices)}
    for u, v, w in edges:
        graph[u].append((v, w))
        
    for u in graph:
        graph[u].sort(key=lambda edge: (edge[0], edge[1]))

    # Track distances and operation summary metrics
    distances = [float('inf')] * num_vertices
    distances[source] = 0

    heap_pushes = 0
    heap_pops = 0
    edges_processed = 0
    settled_nodes = 0

    # Initialize priority queue
    min_heap: List[Tuple[int, int]] = [(0, source)]
    heap_pushes += 1

    while min_heap:
        current_dist, u = heapq.heappop(min_heap)
        heap_pops += 1

        # Skip outdated duplicate entries
        if current_dist > distances[u]:
            continue

        settled_nodes += 1

        # Relax adjacent edges
        for v, weight in graph[u]:
            edges_processed += 1
            new_dist = current_dist + weight

            if new_dist < distances[v]:
                distances[v] = new_dist
                heapq.heappush(min_heap, (new_dist, v))
                heap_pushes += 1

    # Convert unreachable vertices (float('inf')) to -1
    result_distances = [int(d) if d != float('inf') else -1 for d in distances]

    if not include_summary:
        return result_distances

    operation_summary = {
        "edges_processed": edges_processed,
        "heap_pushes": heap_pushes,
        "heap_pops": heap_pops,
        "settled_nodes": settled_nodes
    }

    return result_distances, operation_summary


# --- Demonstration ---
if __name__ == "__main__":
    n = 5
    edges = [
        (0, 1, 4),
        (0, 2, 1),
        (2, 1, 2),
        (1, 3, 1),
        (2, 3, 5),
    ]
    src = 0

    # Standard backwards-compatible call
    dist_only = single_source_route_analyzer(n, edges, src)
    print("Standard Result:", dist_only)

    # Enhanced call with operation summary
    dist, summary = single_source_route_analyzer(n, edges, src, include_summary=True)
    print("\nEnhanced Result:")
    print("Distances:", dist)
    print("Operation Summary:", summary)