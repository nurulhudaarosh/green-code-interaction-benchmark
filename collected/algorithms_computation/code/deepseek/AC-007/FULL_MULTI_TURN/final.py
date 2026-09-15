import sys
from typing import List, Tuple

class DSU:
    """Disjoint Set Union (Union-Find) with path compression and union by rank."""
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """Find the root with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """
        Union two sets. Returns True if merged, False if already connected.
        Uses union by rank for efficiency.
        """
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank: attach smaller rank tree under larger rank tree
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            # Equal ranks: attach root_y under root_x and increment rank of root_x
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True


def minimum_spanning_forest(
    n: int,
    edges: List[Tuple[int, int, int]]
) -> Tuple[int, List[int]]:
    """
    Compute minimum spanning forest using Kruskal's algorithm.
    
    Args:
        n: Number of vertices (0 to n-1)
        edges: List of (u, v, weight) tuples
        
    Returns:
        Tuple of (total_cost, list_of_selected_edge_ids)
        Edge IDs are 0-indexed positions in the input edges list.
        Equal weights are processed by ascending edge ID.
        
    Handles boundary cases:
        - n = 0: returns (0, [])
        - n = 1: handles self-loops correctly
        - m = 0: returns (0, [])
        - Self-loops: ignored (they never connect different components)
        - Parallel edges: processed by weight and ID
        - Disconnected graph: produces forest
    """
    # Boundary case: no vertices
    if n <= 0:
        return 0, []
    
    # Boundary case: no edges
    if not edges:
        return 0, []
    
    # Create list of (weight, u, v, edge_id) and sort
    # Sort by weight primarily, then by edge_id for deterministic tie-breaking
    sorted_edges = []
    for edge_id, (u, v, weight) in enumerate(edges):
        # Handle self-loops: they can never be in a forest
        # But we still include them in processing (they'll be rejected)
        sorted_edges.append((weight, u, v, edge_id))
    
    # Key: sort by weight, then by edge ID (as required)
    sorted_edges.sort(key=lambda x: (x[0], x[3]))
    
    dsu = DSU(n)
    total_cost = 0
    selected_edges = []
    
    for weight, u, v, edge_id in sorted_edges:
        # Validate vertices (just in case of malformed input)
        if u < 0 or u >= n or v < 0 or v >= n:
            continue  # Skip invalid edges
            
        if dsu.union(u, v):
            total_cost += weight
            selected_edges.append(edge_id)
    
    # Return edge IDs in ascending order as required
    return total_cost, sorted(selected_edges)


def parse_input() -> Tuple[int, List[Tuple[int, int, int]]]:
    """Parse input from stdin with robust error handling."""
    data = sys.stdin.read().strip().split()
    if not data:
        return 0, []
    
    try:
        # First two values: n and m
        n = int(data[0])
        m = int(data[1])
    except (IndexError, ValueError):
        return 0, []
    
    edges = []
    idx = 2
    for i in range(m):
        try:
            if idx + 2 >= len(data):
                break
            u = int(data[idx])
            v = int(data[idx + 1])
            w = int(data[idx + 2])
            edges.append((u, v, w))
            idx += 3
        except (IndexError, ValueError):
            break
    
    return n, edges


def test_boundary_cases():
    """Test function for boundary cases - not called in normal execution."""
    print("Testing boundary cases...")
    
    # Test 1: n = 0
    result = minimum_spanning_forest(0, [(0, 1, 5)])
    assert result == (0, []), f"Test 1 failed: {result}"
    print("✓ Test 1: n = 0")
    
    # Test 2: n = 1, no edges
    result = minimum_spanning_forest(1, [])
    assert result == (0, []), f"Test 2 failed: {result}"
    print("✓ Test 2: n = 1, m = 0")
    
    # Test 3: n = 1, self-loops only
    result = minimum_spanning_forest(1, [(0, 0, 5), (0, 0, 3)])
    assert result == (0, []), f"Test 3 failed: {result}"
    print("✓ Test 3: n = 1, self-loops only")
    
    # Test 4: n = 2, m = 0
    result = minimum_spanning_forest(2, [])
    assert result == (0, []), f"Test 4 failed: {result}"
    print("✓ Test 4: n = 2, m = 0")
    
    # Test 5: Self-loop with valid edge
    edges = [(0, 1, 5), (0, 0, 3), (1, 2, 4)]
    result = minimum_spanning_forest(3, edges)
    assert result == (9, [0, 2]), f"Test 5 failed: {result}"
    print("✓ Test 5: Self-loop with valid edges")
    
    # Test 6: Parallel edges with tie-breaking
    edges = [(0, 1, 5), (0, 1, 3), (0, 1, 4)]
    result = minimum_spanning_forest(2, edges)
    assert result == (3, [1]), f"Test 6 failed: {result}"
    print("✓ Test 6: Parallel edges")
    
    # Test 7: Disconnected graph
    edges = [(0, 1, 5), (2, 3, 3), (1, 2, 4)]
    result = minimum_spanning_forest(4, edges)
    # Should select (2,3) weight 3, (1,2) weight 4, (0,1) weight 5 = 12
    assert result == (12, [0, 1, 2]), f"Test 7 failed: {result}"
    print("✓ Test 7: Disconnected graph")
    
    # Test 8: Equal weights with tie-breaking by ID
    edges = [(0, 1, 5), (1, 2, 5), (2, 3, 5), (0, 3, 5)]
    result = minimum_spanning_forest(4, edges)
    # Should select edge 0, 1, 2 (lowest IDs) = 15
    assert result == (15, [0, 1, 2]), f"Test 8 failed: {result}"
    print("✓ Test 8: Equal weights tie-breaking")
    
    # Test 9: Large weight values
    edges = [(0, 1, 10**9), (1, 2, 10**9), (0, 2, 2*10**9)]
    result = minimum_spanning_forest(3, edges)
    assert result == (2*10**9, [0, 1]), f"Test 9 failed: {result}"
    print("✓ Test 9: Large weights")
    
    # Test 10: Single vertex with multiple self-loops and no valid edges
    result = minimum_spanning_forest(1, [(0, 0, 1), (0, 0, 2), (0, 0, 3)])
    assert result == (0, []), f"Test 10 failed: {result}"
    print("✓ Test 10: Multiple self-loops only")
    
    print("\nAll boundary tests passed! ✓")


def main():
    """Main entry point."""
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_boundary_cases()
        return
    
    n, edges = parse_input()
    
    # Boundary case handling
    if n <= 0:
        print(0)
        print()
        return
    
    total_cost, selected_ids = minimum_spanning_forest(n, edges)
    
    # Original output format (unchanged)
    print(total_cost)
    if selected_ids:
        print(" ".join(map(str, selected_ids)))
    else:
        print()  # Empty second line when no edges selected


if __name__ == "__main__":
    main()