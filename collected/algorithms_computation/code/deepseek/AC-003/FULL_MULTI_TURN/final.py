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

Output Format:
- Single line: N space-separated integers representing shortest distances
- Use -1 for unreachable vertices

Constraints:
- 1 ≤ N ≤ 10^5
- 0 ≤ M ≤ 10^5
- 0 ≤ u, v < N
- 0 ≤ w ≤ 10^9
- Source vertex S is 0-indexed

Algorithm: Dijkstra's Algorithm with Binary Heap (Priority Queue)
- Time Complexity: O((N + M) log N)
- Space Complexity: O(N + M)
- Deterministic tie handling: uses > comparison
- Handles all boundary cases including max values
"""

import sys
import heapq
from typing import List, Tuple, Optional


def dijkstra(
    n: int,
    adj: List[List[Tuple[int, int]]],
    source: int
) -> List[int]:
    """
    Compute shortest distances from source to all vertices using Dijkstra's algorithm.
    Handles all boundary cases including large weights and graph sizes.

    Args:
        n: Number of vertices (1 to 10^5)
        adj: Adjacency list where adj[u] = [(v, weight), ...]
        source: Source vertex (0-indexed)

    Returns:
        List of shortest distances from source to each vertex
        -1 for unreachable vertices

    Time Complexity: O((N + M) log N)
    Space Complexity: O(N + M)
    """
    # Use a very large number that exceeds any possible path sum
    # Max path: (N-1) * max_weight = 10^5 * 10^9 = 10^14
    # So 10^18 is safely larger than any possible distance
    INF = 10**18
    
    # Initialize distances
    dist = [INF] * n
    dist[source] = 0
    
    # Priority queue: (distance, vertex)
    # Python's heap with tuple provides deterministic ordering:
    # - Primary: distance (ascending)
    # - Secondary: vertex index (ascending) for tie-breaking
    pq = [(0, source)]
    
    # Track processed vertices for early termination
    processed_count = 0
    
    while pq and processed_count < n:
        d, u = heapq.heappop(pq)
        
        # Skip if we've already found a better path
        # Using > for robust handling (more precise than !=)
        if d > dist[u]:
            continue
        
        # Mark as processed (each vertex processed at most once)
        processed_count += 1
        
        # Relax all outgoing edges
        for v, weight in adj[u]:
            # Check for overflow prevention (though Python handles big ints)
            new_dist = d + weight
            
            # Only update if we found a shorter path
            if new_dist < dist[v]:
                dist[v] = new_dist
                heapq.heappush(pq, (new_dist, v))
    
    # Convert INF to -1 for unreachable vertices
    return [-1 if d == INF else d for d in dist]


def solve() -> None:
    """
    Read input, run Dijkstra's algorithm, and print results.
    Handles all boundary cases including empty input and malformed data.
    """
    # Read all input at once for efficiency
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    
    # Parse first line: N, M, S
    idx = 0
    try:
        n = int(data[idx])
        idx += 1
        m = int(data[idx])
        idx += 1
        s = int(data[idx])
        idx += 1
    except (IndexError, ValueError):
        # Invalid input format
        return
    
    # Validate constraints
    if not (1 <= n <= 100000):
        # Invalid N
        return
    if not (0 <= m <= 100000):
        # Invalid M
        return
    if not (0 <= s < n):
        # Invalid source
        return
    
    # Build adjacency list
    adj: List[List[Tuple[int, int]]] = [[] for _ in range(n)]
    
    # Track if we have multiple edges for a given pair
    # We'll keep all edges but Dijkstra will naturally handle them
    # This is more memory efficient for large graphs
    
    # Read all edges
    edges_read = 0
    for _ in range(m):
        if idx + 2 >= len(data):
            break
            
        try:
            u = int(data[idx])
            idx += 1
            v = int(data[idx])
            idx += 1
            w = int(data[idx])
            idx += 1
        except (IndexError, ValueError):
            break
        
        # Validate edge constraints
        if 0 <= u < n and 0 <= v < n and 0 <= w <= 10**9:
            adj[u].append((v, w))
            edges_read += 1
    
    # If we couldn't read all edges, still proceed with what we have
    
    # Run Dijkstra's algorithm
    distances = dijkstra(n, adj, s)
    
    # Print results
    print(' '.join(str(d) for d in distances))


# Test functions for boundary cases
def run_tests() -> None:
    """
    Run test cases for all boundary conditions.
    """
    print("Running boundary tests...")
    print("=" * 60)
    
    test_cases = [
        # Test 1: Minimum N (1 vertex)
        {
            'name': 'Single vertex',
            'input': '1 0 0\n',
            'expected': '0'
        },
        
        # Test 2: No edges
        {
            'name': 'No edges, multiple vertices',
            'input': '3 0 1\n',
            'expected': '-1 0 -1'
        },
        
        # Test 3: Maximum edge weight
        {
            'name': 'Maximum edge weight (10^9)',
            'input': '2 1 0\n0 1 1000000000\n',
            'expected': '0 1000000000'
        },
        
        # Test 4: Zero weight edges
        {
            'name': 'Zero weight edges',
            'input': '3 2 0\n0 1 0\n1 2 0\n',
            'expected': '0 0 0'
        },
        
        # Test 5: Self-loops
        {
            'name': 'Self-loops',
            'input': '2 2 0\n0 0 5\n0 1 3\n',
            'expected': '0 3'
        },
        
        # Test 6: Multiple edges (should take shortest)
        {
            'name': 'Multiple edges',
            'input': '3 3 0\n0 1 5\n0 1 3\n1 2 1\n',
            'expected': '0 3 4'
        },
        
        # Test 7: Source at last vertex
        {
            'name': 'Source at last vertex',
            'input': '3 2 2\n0 2 5\n1 2 3\n',
            'expected': '-1 -1 0'
        },
        
        # Test 8: Large graph with long path
        {
            'name': 'Long path with large sum',
            'input': '4 3 0\n0 1 500000000\n1 2 500000000\n2 3 500000000\n',
            'expected': '0 500000000 1000000000 1500000000'
        },
        
        # Test 9: Dense graph (complete)
        {
            'name': 'Complete graph (3 vertices)',
            'input': '3 6 0\n0 1 1\n0 2 4\n1 0 2\n1 2 1\n2 0 3\n2 1 5\n',
            'expected': '0 1 2'
        },
        
        # Test 10: Disconnected graph
        {
            'name': 'Disconnected graph',
            'input': '5 3 0\n0 1 1\n1 2 2\n3 4 3\n',
            'expected': '0 1 3 -1 -1'
        },
        
        # Test 11: All zero-weight cycles
        {
            'name': 'Zero-weight cycle',
            'input': '3 3 0\n0 1 0\n1 2 0\n2 0 0\n',
            'expected': '0 0 0'
        },
        
        # Test 12: Large N with sparse edges
        {
            'name': 'Large graph (5 vertices, 2 edges)',
            'input': '5 2 0\n0 4 10\n4 3 20\n',
            'expected': '0 -1 -1 30 10'
        },
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        # Simulate input
        sys.stdin = type('Mock', (), {'buffer': type('Mock', (), {'read': lambda x: test['input'].encode()})()})()
        
        # Capture output
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        try:
            solve()
            output = sys.stdout.getvalue().strip()
            
            # Check result
            if output == test['expected']:
                print(f"✓ Test {i}: {test['name']}")
                passed += 1
            else:
                print(f"✗ Test {i}: {test['name']}")
                print(f"  Expected: {test['expected']}")
                print(f"  Got:      {output}")
                failed += 1
        except Exception as e:
            print(f"✗ Test {i}: {test['name']} - Exception: {e}")
            failed += 1
        finally:
            sys.stdout = old_stdout
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print()


if __name__ == "__main__":
    # Check if we're running tests or solving
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_tests()
    else:
        solve()