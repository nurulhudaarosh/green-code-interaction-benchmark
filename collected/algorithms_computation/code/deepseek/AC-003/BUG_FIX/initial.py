"""
Shortest Path from Single Source in Directed Graph with Non-negative Weights
---------------------------------------------------------------------------
Problem:
- Given a directed graph with N vertices (0-indexed) and M edges.
- Each edge has a non-negative weight.
- Source vertex is given.
- Compute the shortest distance from source to every vertex.
- Unreachable vertices should have distance -1.

Constraints (typical):
- 1 <= N <= 10^5
- 0 <= M <= 2*10^5
- 0 <= weight <= 10^9
- Source is a valid vertex.

Required Output:
- A list of length N where ans[i] is the shortest distance from source to i,
  or -1 if vertex i is unreachable.

Algorithm:
- Use Dijkstra's algorithm with a binary heap (priority queue).
- Graph represented as adjacency list: adj[u] = [(v, weight), ...]
- Time Complexity: O((N + M) log N)
- Space Complexity: O(N + M)

Implementation Details:
- Use heapq for binary heap.
- Distances initialized to infinity (float('inf')).
- Distance to source = 0.
- While heap not empty, pop (dist, u). If dist > dist[u], skip.
- For each neighbor (v, w), if dist[u] + w < dist[v], update and push.
- Convert unreachable (inf) to -1 before returning.
"""

import heapq
from typing import List, Tuple

def dijkstra(n: int, adj: List[List[Tuple[int, int]]], src: int) -> List[int]:
    """
    Computes shortest distances from source to all vertices using Dijkstra's algorithm.

    Args:
        n: Number of vertices (0 to n-1).
        adj: Adjacency list where adj[u] contains (v, weight) for directed edge u -> v.
        src: Source vertex.

    Returns:
        List of shortest distances, with -1 for unreachable vertices.
    """
    INF = 10**18  # Use a large number (greater than max possible distance)
    dist = [INF] * n
    dist[src] = 0

    # Min-heap: (distance, vertex)
    heap = [(0, src)]

    while heap:
        d, u = heapq.heappop(heap)

        # If we already have a better distance, skip
        if d != dist[u]:
            continue

        # Explore neighbors
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    # Convert unreachable distances to -1
    return [-1 if d == INF else d for d in dist]


def solve() -> None:
    """
    Sample usage:
    Reads graph from standard input or uses a hardcoded example.
    Format (for STDIN):
    First line: N M (vertices, edges)
    Next M lines: u v w (directed edge u -> v with weight w)
    Last line: source
    """
    import sys

    # Uncomment the following block for STDIN input:
    # data = sys.stdin.read().strip().split()
    # if not data:
    #     return
    # it = iter(data)
    # n = int(next(it))
    # m = int(next(it))
    # adj = [[] for _ in range(n)]
    # for _ in range(m):
    #     u = int(next(it))
    #     v = int(next(it))
    #     w = int(next(it))
    #     adj[u].append((v, w))
    # src = int(next(it))

    # Example usage (hardcoded for demonstration):
    # Graph: 4 vertices, 5 edges
    # 0 -> 1 (weight 4)
    # 0 -> 2 (weight 1)
    # 2 -> 1 (weight 2)
    # 1 -> 3 (weight 1)
    # 2 -> 3 (weight 5)
    # Source = 0
    n = 4
    adj = [
        [(1, 4), (2, 1)],
        [(3, 1)],
        [(1, 2), (3, 5)],
        []
    ]
    src = 0

    distances = dijkstra(n, adj, src)
    print(distances)  # Expected: [0, 3, 1, 4]


if __name__ == "__main__":
    solve()