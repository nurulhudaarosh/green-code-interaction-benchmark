import sys
from typing import List, Tuple, Optional

class DSU:
    """Disjoint Set Union (Union-Find) data structure with path compression and union by rank."""
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        """Find the root of element x with path compression."""
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        """Union two sets. Returns True if they were merged, False if already connected."""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return False
        
        # Union by rank
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1
        
        return True


def minimum_spanning_forest(
    n: int, 
    edges: List[Tuple[int, int, int]]
) -> Tuple[int, List[int]]:
    """
    Find the minimum spanning forest of an undirected weighted graph.
    
    Args:
        n: Number of vertices (0 to n-1)
        edges: List of tuples (u, v, weight) representing edges
    
    Returns:
        Tuple of (total_cost, selected_edge_ids)
        selected_edge_ids: List of original edge indices (0-based) in the MST forest
    """
    if n <= 0:
        return 0, []
    
    # Create list of (weight, u, v, original_index)
    indexed_edges = [(weight, u, v, idx) for idx, (u, v, weight) in enumerate(edges)]
    
    # Sort by weight, then by original ID for tie-breaking
    # We don't need to explicitly sort by ID if we store the index and sort stably,
    # but to be deterministic, we'll sort by (weight, original_index)
    indexed_edges.sort(key=lambda x: (x[0], x[3]))
    
    dsu = DSU(n)
    total_cost = 0
    selected_edges = []
    
    for weight, u, v, idx in indexed_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edges.append(idx)
    
    return total_cost, selected_edges


def main():
    """Main function to read input and output the result."""
    # Read input
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    it = iter(data)
    n = int(next(it))
    m = int(next(it))
    
    edges = []
    for _ in range(m):
        u = int(next(it))
        v = int(next(it))
        w = int(next(it))
        edges.append((u, v, w))
    
    # Find minimum spanning forest
    total_cost, selected_edges = minimum_spanning_forest(n, edges)
    
    # Output results
    print(total_cost)
    if selected_edges:
        print(" ".join(str(eid) for eid in sorted(selected_edges)))
    else:
        print()


if __name__ == "__main__":
    main()