#!/usr/bin/env python3
"""
Shortest Path from Source to All Vertices using Dijkstra's Algorithm

Problem:
- Given a directed graph with non-negative edge weights and a source vertex
- Compute the shortest distance from the source to every vertex
- Use -1 for unreachable vertices

Input Format:
- First line: N M S (number of vertices, number of edges, source vertex)
- Next M lines: u v w (directed edge from u to v with weight w)
- Vertices are 0-indexed

Output Format (Original):
- Single line: N space-sparated integers representing shortest distances
- Use -1 for unreachable vertices

Output Format (With Summary Feature):
- First line: N space-sparated integers representing shortest distances
- Second line: operation_summary with deterministic counts

Constraints:
- 1 ≤ N ≤ 10^5
- 0 ≤ M ≤ 10^5
- 0 ≤ u, v < N
- 0 ≤ w ≤ 10^9
- Source vertex S is 0-indexed

Algorithm: Dijkstra's Algorithm with Binary Heap (Priority Queue)
- Time Complexity: O((N + M) log N)
- Space Complexity: O(N + M)
- Deterministic tie handling: uses > comparison instead of !=
"""

import sys
import heapq
from typing import List, Tuple, Dict, Optional


def dijkstra(
    n: int,
    adj: List[List[Tuple[int, int]]],
    source: int,
    track_operations: bool = False
) -> Tuple[List[int], Optional[Dict[str, int]]]:
    """
    Compute shortest distances from source to all vertices using Dijkstra's algorithm.

    Args:
        n: Number of vertices
        adj: Adjacency list where adj[u] = [(v, weight), ...]
        source: Source vertex (0-indexed)
        track_operations: If True, return operation summary

    Returns:
        Tuple of (distances, operation_summary)
        - distances: List of shortest distances, -1 for unreachable
        - operation_summary: Dict with operation counts or None if not tracked
    """
    # Initialize distances with a large number
    INF = 10**18
    dist = [INF] * n
    dist[source] = 0

    # Priority queue: (distance, vertex)
    pq = [(0, source)]

    # Operation counters
    operations = {
        'vertices_processed': 0,
        'successful_relaxations': 0,
        'heap_push_operations': 1,  # Initial push of source
        'heap_pop_operations': 0,
    }

    while pq:
        d, u = heapq.heappop(pq)
        operations['heap_pop_operations'] += 1

        # Skip if we've already found a better path
        if d > dist[u]:
            continue

        # Process this vertex
        operations['vertices_processed'] += 1

        # Relax all outgoing edges
        for v, weight in adj[u]:
            new_dist = d + weight
            if new_dist < dist[v]:
                dist[v] = new_dist
                heapq.heappush(pq, (new_dist, v))
                operations['heap_push_operations'] += 1
                operations['successful_relaxations'] += 1

    # Convert INF to -1 for unreachable vertices
    result_dist = [-1 if d == INF else d for d in dist]

    if track_operations:
        # Add derived metrics
        operations['total_heap_operations'] = (
            operations['heap_push_operations'] + 
            operations['heap_pop_operations']
        )
        return result_dist, operations
    else:
        return result_dist, None


def solve() -> None:
    """
    Read input, run Dijkstra's algorithm, and print results.
    Supports optional summary feature via environment variable or command-line flag.
    """
    # Read all input at once for efficiency
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    # Parse first line: N, M, S
    idx = 0
    n = int(data[idx])
    idx += 1
    m = int(data[idx])
    idx += 1
    s = int(data[idx])
    idx += 1

    # Check if summary feature is requested
    # Can be enabled via: --summary flag in args or SUMMARY=1 environment variable
    enable_summary = False
    
    # Check for command-line flag if there are extra arguments
    # We'll check if any argument starts with '--summary'
    # Since we're reading from stdin, we need to handle args differently
    if len(sys.argv) > 1:
        enable_summary = any('--summary' in arg for arg in sys.argv)
    
    # Also check environment variable (if set in system)
    import os
    if os.environ.get('SUMMARY') == '1':
        enable_summary = True

    # Build adjacency list
    adj: List[List[Tuple[int, int]]] = [[] for _ in range(n)]

    for _ in range(m):
        u = int(data[idx])
        idx += 1
        v = int(data[idx])
        idx += 1
        w = int(data[idx])
        idx += 1

        # Validate input constraints
        if 0 <= u < n and 0 <= v < n and w >= 0:
            adj[u].append((v, w))

    # Run Dijkstra's algorithm with optional tracking
    distances, summary = dijkstra(n, adj, s, track_operations=enable_summary)

    # Print results - original format always preserved
    print(' '.join(str(d) for d in distances))

    # Print summary if feature is enabled
    if enable_summary and summary is not None:
        print(f"operation_summary: {summary}")


if __name__ == "__main__":
    solve()