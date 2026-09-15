#!/usr/bin/env python3
"""
Shortest Path from Source to All Vertices using Dijkstra's Algorithm

Problem:
Given a directed graph with non-negative edge weights and a source vertex,
compute the shortest distance from the source to every vertex.

Input:
- n: number of vertices (0 to n-1)
- edges: list of (u, v, w) where u->v has weight w (w >= 0)
- source: source vertex

Output:
- List of distances where dist[i] is the shortest distance from source to i,
  or -1 if vertex i is unreachable.

Constraints:
- 1 <= n <= 10^5
- 0 <= w <= 10^9
- Edges may contain duplicates
- No negative weights

Algorithm:
- Use adjacency lists for graph representation
- Dijkstra's algorithm with binary heap (heapq)
- Time complexity: O((V + E) log V)
- Space complexity: O(V + E)
"""

import heapq
from typing import List, Tuple


def dijkstra(n: int, edges: List[Tuple[int, int, int]], source: int) -> List[int]:
    """
    Compute shortest distances from source to all vertices.

    Args:
        n: Number of vertices (0 to n-1)
        edges: List of directed edges as (u, v, weight)
        source: Source vertex

    Returns:
        List of distances where -1 means unreachable
    """
    # Build adjacency list
    adj = [[] for _ in range(n)]
    for u, v, w in edges:
        adj[u].append((v, w))

    # Initialize distances
    INF = float('inf')
    dist = [INF] * n
    dist[source] = 0

    # Min-heap: (distance, vertex)
    heap = [(0, source)]

    while heap:
        d, u = heapq.heappop(heap)

        # Skip if we have a better distance already
        if d > dist[u]:
            continue

        # Relax edges from u
        for v, w in adj[u]:
            new_dist = d + w
            if new_dist < dist[v]:
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    # Convert INF to -1 for unreachable vertices
    return [-1 if d == INF else d for d in dist]


def main():
    """
    Example usage and test cases.
    """
    # Test case 1: Simple graph
    print("Test Case 1: Simple graph")
    n = 5
    edges = [
        (0, 1, 10),
        (0, 2, 5),
        (1, 2, 2),
        (1, 3, 1),
        (2, 1, 3),
        (2, 3, 9),
        (2, 4, 2),
        (3, 4, 4),
        (4, 3, 6)
    ]
    source = 0
    result = dijkstra(n, edges, source)
    print(f"Distances from source {source}: {result}")
    # Expected: [0, 8, 5, 9, 7]

    # Test case 2: Disconnected graph
    print("\nTest Case 2: Disconnected graph")
    n = 4
    edges = [
        (0, 1, 5),
        (2, 3, 3)
    ]
    source = 0
    result = dijkstra(n, edges, source)
    print(f"Distances from source {source}: {result}")
    # Expected: [0, 5, -1, -1]

    # Test case 3: Single vertex
    print("\nTest Case 3: Single vertex")
    n = 1
    edges = []
    source = 0
    result = dijkstra(n, edges, source)
    print(f"Distances from source {source}: {result}")
    # Expected: [0]

    # Test case 4: Duplicate edges
    print("\nTest Case 4: Duplicate edges")
    n = 3
    edges = [
        (0, 1, 5),
        (0, 1, 3),
        (1, 2, 2)
    ]
    source = 0
    result = dijkstra(n, edges, source)
    print(f"Distances from source {source}: {result}")
    # Expected: [0, 3, 5]

    # Test case 5: Large weights
    print("\nTest Case 5: Large weights")
    n = 3
    edges = [
        (0, 1, 10**9),
        (1, 2, 10**9)
    ]
    source = 0
    result = dijkstra(n, edges, source)
    print(f"Distances from source {source}: {result}")
    # Expected: [0, 1000000000, 2000000000]

    # Test case 6: Self-loop
    print("\nTest Case 6: Self-loop")
    n = 3
    edges = [
        (0, 0, 5),
        (0, 1, 2),
        (1, 2, 3)
    ]
    source = 0
    result = dijkstra(n, edges, source)
    print(f"Distances from source {source}: {result}")
    # Expected: [0, 2, 5]


if __name__ == "__main__":
    main()