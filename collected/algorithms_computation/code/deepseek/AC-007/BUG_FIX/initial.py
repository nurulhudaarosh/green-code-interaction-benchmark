import sys
from typing import List, Tuple, Optional


class DSU:
    """Disjoint Set Union (Union-Find) data structure with path compression and union by rank."""
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """Find the representative of the set containing x with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """Union the sets containing x and y. Returns True if they were in different sets."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        
        # Union by rank
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


def minimum_spanning_forest(n: int, edges: List[Tuple[int, int, int, int]]) -> Tuple[int, List[int]]:
    """
    Find the minimum spanning forest of an undirected weighted graph.
    
    Args:
        n: Number of vertices (0 to n-1)
        edges: List of (u, v, weight, id) where id is the original edge ID
        
    Returns:
        Tuple of (total_cost, list_of_selected_edge_ids)
        
    Equal-cost edges are processed by original ID (ascending) for determinism.
    """
    if n == 0:
        return 0, []
    
    # Sort edges by (weight, id) for deterministic tie-breaking
    sorted_edges = sorted(edges, key=lambda x: (x[2], x[3]))
    
    dsu = DSU(n)
    total_cost = 0
    selected_ids = []
    
    for u, v, weight, edge_id in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_ids.append(edge_id)
    
    return total_cost, selected_ids


def solve() -> None:
    """
    Read input from stdin and output the result.
    
    Input format:
    First line: n m (number of vertices, number of edges)
    Next m lines: u v w (edge between u and v with weight w)
    Edges are numbered from 0 to m-1 in the order they appear.
    
    Output format:
    First line: total_cost
    Second line: space-separated selected edge IDs (in ascending order)
    """
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    it = iter(data)
    n = int(next(it))
    m = int(next(it))
    
    edges = []
    for edge_id in range(m):
        u = int(next(it))
        v = int(next(it))
        w = int(next(it))
        edges.append((u, v, w, edge_id))
    
    total_cost, selected_ids = minimum_spanning_forest(n, edges)
    
    # Output the result
    print(total_cost)
    if selected_ids:
        # Sort selected IDs in ascending order for consistent output
        selected_ids.sort()
        print(' '.join(map(str, selected_ids)))
    else:
        # Print empty line if no edges selected (forest with isolated vertices)
        print()


# Example usage for testing
if __name__ == "__main__":
    # Example test case
    test_input = """4 5
0 1 1
1 2 2
2 3 3
0 3 4
1 3 5
"""
    # Redirect stdin for testing
    import io
    sys.stdin = io.StringIO(test_input)
    solve()