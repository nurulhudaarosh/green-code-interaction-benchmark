"""
Shortest Path from Single Source in Directed Graph with Non-negative Weights
---------------------------------------------------------------------------
Problem:
- Given a directed graph with N vertices (0-indexed) and M edges.
- Each edge has a non-negative weight.
- Source vertex is given.
- Compute the shortest distance from source to every vertex.
- Unreachable vertices should have distance -1.
- MUST use adjacency lists and Dijkstra's algorithm with a binary heap.
- MUST have deterministic tie handling: when distances are equal, 
  process vertices in ascending vertex ID order.

Constraints:
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
- For deterministic tie handling: heap stores (distance, vertex_id)
- When two distances are equal, heapq will compare vertex_id (ascending)
- This ensures consistent processing order
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
        Deterministic: equal distances processed by vertex ID ascending.
    """
    INF = 10**18
    dist = [INF] * n
    dist[src] = 0
    
    # Heap stores (distance, vertex) - heapq will compare vertex ID on ties
    # This gives deterministic tie-breaking (lower vertex ID first)
    heap = [(0, src)]
    
    # Track visited to avoid redundant processing (optional optimization)
    # Not strictly needed but helps with determinism
    visited = [False] * n
    
    while heap:
        d, u = heapq.heappop(heap)
        
        # Skip if already processed
        if visited[u]:
            continue
        
        # Mark as visited (processed)
        visited[u] = True
        
        # If this entry is stale, skip
        if d != dist[u]:
            continue
        
        # Explore neighbors
        # Sort neighbors for deterministic edge exploration (optional but good practice)
        # The heapq tie-breaking already ensures vertex processing order, but
        # sorting neighbors ensures edge order is deterministic too
        for v, w in sorted(adj[u]):  # Sort by vertex ID for deterministic neighbor iteration
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    
    # Convert unreachable distances to -1
    return [-1 if d == INF else d for d in dist]


def solve() -> None:
    """
    Sample usage with deterministic tie-handling demonstration.
    """
    # Test case 1: Multiple paths with equal distances
    # Graph: 4 vertices
    # 0->1 (weight 1), 0->2 (weight 1), 1->3 (weight 0), 2->3 (weight 0)
    # Source: 0
    # Expected: [0, 1, 1, 1] (deterministic: 1 processed before 2)
    n1 = 4
    adj1 = [
        [(1, 1), (2, 1)],
        [(3, 0)],
        [(3, 0)],
        []
    ]
    src1 = 0
    result1 = dijkstra(n1, adj1, src1)
    print(f"Test 1: {result1}")  # Expected: [0, 1, 1, 1]
    
    # Test case 2: Zero-weight cycle
    # 0->1 (weight 0), 1->2 (weight 0), 0->2 (weight 0)
    # Source: 0
    # Expected: [0, 0, 0]
    n2 = 3
    adj2 = [
        [(1, 0), (2, 0)],
        [(2, 0)],
        []
    ]
    src2 = 0
    result2 = dijkstra(n2, adj2, src2)
    print(f"Test 2: {result2}")  # Expected: [0, 0, 0]
    
    # Test case 3: Unreachable vertex
    # 0->1 (weight 5), 2 isolated
    # Source: 0
    # Expected: [0, 5, -1]
    n3 = 3
    adj3 = [
        [(1, 5)],
        [],
        []
    ]
    src3 = 0
    result3 = dijkstra(n3, adj3, src3)
    print(f"Test 3: {result3}")  # Expected: [0, 5, -1]
    
    # Test case 4: Deterministic tie-handling demonstration
    # Multiple vertices at same distance, processing order matters for updates
    # 0->1 (weight 2), 0->2 (weight 2), 1->3 (weight 1), 2->3 (weight 1)
    # Both paths to 3 have equal cost (3), deterministic processing ensures
    # vertex 1 is processed before vertex 2 (since 1 < 2)
    n4 = 4
    adj4 = [
        [(1, 2), (2, 2)],
        [(3, 1)],
        [(3, 1)],
        []
    ]
    src4 = 0
    result4 = dijkstra(n4, adj4, src4)
    print(f"Test 4: {result4}")  # Expected: [0, 2, 2, 3]


if __name__ == "__main__":
    solve()