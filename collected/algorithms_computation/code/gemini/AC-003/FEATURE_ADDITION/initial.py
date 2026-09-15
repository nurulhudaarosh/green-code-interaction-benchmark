import heapq
from typing import List, Tuple

def dijkstra_shortest_paths(num_vertices: int, adj_list: List[List[Tuple[int, int]]], source: int) -> List[int]:
    """
    Computes shortest distances from source to all vertices using Dijkstra's algorithm.

    :param num_vertices: Total number of vertices in the graph (0 to num_vertices - 1).
    :param adj_list: Adjacency list where adj_list[u] contains tuples of (neighbor_v, weight).
    :param source: The starting source vertex index.
    :return: List of shortest distances from source to each vertex (-1 if unreachable).
    """
    # Initialize distances to infinity
    distances = [float('inf')] * num_vertices
    distances[source] = 0

    # Min-heap priority queue storing tuples: (distance, vertex)
    min_heap = [(0, source)]

    while min_heap:
        current_dist, u = heapq.heappop(min_heap)

        # Skip stale heap entries
        if current_dist > distances[u]:
            continue

        # Relax adjacent edges
        for v, weight in adj_list[u]:
            distance_through_u = current_dist + weight

            if distance_through_u < distances[v]:
                distances[v] = distance_through_u
                heapq.heappush(min_heap, (distance_through_u, v))

    # Convert unreachable vertices (infinity) to -1
    return [dist if dist != float('inf') else -1 for dist in distances]


# --- Example Usage ---
if __name__ == "__main__":
    # Graph with 5 vertices (0 to 4)
    V = 5
    source_node = 0

    # adj[u] = [(v1, w1), (v2, w2), ...]
    graph = [
        [(1, 4), (2, 1)],  # Node 0 -> Node 1 (w=4), Node 2 (w=1)
        [(3, 1)],          # Node 1 -> Node 3 (w=1)
        [(1, 2), (3, 5)],  # Node 2 -> Node 1 (w=2), Node 3 (w=5)
        [],                # Node 3 has no outgoing edges
        []                 # Node 4 is unreachable from node 0
    ]

    result = dijkstra_shortest_paths(V, graph, source_node)
    print("Shortest distances from source:", result)
    # Expected Output: [0, 3, 1, 4, -1]