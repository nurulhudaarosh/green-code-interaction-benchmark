import heapq

def single_source_route_analyzer(
    num_vertices: int, 
    edges: list[tuple[int, int, int]], 
    source: int
) -> list[int]:
    """
    Computes shortest distances from a single source vertex to all vertices in a directed graph.
    
    :param num_vertices: Total number of vertices V (indexed 0 to V-1)
    :param edges: List of tuples (u, v, weight) representing directed edges with non-negative weights
    :param source: Starting vertex index (0 <= source < num_vertices)
    :return: List of shortest path costs where index i is the distance to vertex i (-1 if unreachable)
    """
    if num_vertices <= 0:
        return []
    if not (0 <= source < num_vertices):
        raise ValueError(f"Source vertex {source} out of bounds for V = {num_vertices}")

    # Build adjacency list
    graph = [[] for _ in range(num_vertices)]
    for u, v, weight in edges:
        graph[u].append((v, weight))

    # Initialize distances
    distances = [float('inf')] * num_vertices
    distances[source] = 0

    # Min-priority queue: (distance, vertex)
    # Binary heap guarantees deterministic ties based on tuple ordering (distance, vertex_index)
    pq = [(0, source)]

    while pq:
        current_dist, u = heapq.heappop(pq)

        # Skip stale priority queue entries
        if current_dist > distances[u]:
            continue

        for v, weight in graph[u]:
            distance_via_u = current_dist + weight
            
            if distance_via_u < distances[v]:
                distances[v] = distance_via_u
                heapq.heappush(pq, (distance_via_u, v))

    # Convert unreachable representation to -1
    return [d if d != float('inf') else -1 for d in distances]


# --- Comprehensive Test Suite ---
def run_tests():
    # Test 1: Single vertex graph (V = 1, E = 0)
    assert single_source_route_analyzer(1, [], 0) == [0], "Test 1 Failed"

    # Test 2: Disconnected graph (V = 3, E = 0)
    assert single_source_route_analyzer(3, [], 0) == [0, -1, -1], "Test 2 Failed"

    # Test 3: Zero-weight edges and zero-weight cycle
    # 0 -> 1 (wt 0), 1 -> 2 (wt 0), 2 -> 1 (wt 0, self-cycle)
    edges_zero = [(0, 1, 0), (1, 2, 0), (2, 1, 0)]
    assert single_source_route_analyzer(3, edges_zero, 0) == [0, 0, 0], "Test 3 Failed"

    # Test 4: Parallel edges with different weights
    # 0 -> 1 with weights 10 and 2
    edges_parallel = [(0, 1, 10), (0, 1, 2)]
    assert single_source_route_analyzer(2, edges_parallel, 0) == [0, 2], "Test 4 Failed"

    # Test 5: Self-loops
    edges_self_loop = [(0, 0, 5), (0, 1, 3)]
    assert single_source_route_analyzer(2, edges_self_loop, 0) == [0, 3], "Test 5 Failed"

    # Test 6: Linear chain with large weights
    edges_large = [(0, 1, 10**9), (1, 2, 10**9)]
    assert single_source_route_analyzer(3, edges_large, 0) == [0, 10**9, 2 * 10**9], "Test 6 Failed"

    # Test 7: Standard graph with unreachable node
    edges_standard = [(0, 1, 4), (0, 2, 1), (2, 1, 2), (1, 3, 1)]
    assert single_source_route_analyzer(5, edges_standard, 0) == [0, 3, 1, 4, -1], "Test 7 Failed"

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()