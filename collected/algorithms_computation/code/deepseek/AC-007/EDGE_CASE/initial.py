import sys
from typing import List, Tuple

class DSU:
    """Disjoint Set Union data structure with path compression and union by rank."""
    
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


def minimum_spanning_forest(n: int, edges: List[Tuple[int, int, int, int]]) -> Tuple[int, List[int]]:
    """
    Find the minimum spanning forest of an undirected weighted graph.
    
    Args:
        n: Number of vertices (0 to n-1)
        edges: List of (id, u, v, weight) where id is the original edge ID
        
    Returns:
        Tuple of (total_cost, selected_edge_ids)
    """
    # Sort edges by (weight, id) for deterministic tie-breaking
    sorted_edges = sorted(edges, key=lambda x: (x[3], x[0]))
    
    dsu = DSU(n)
    total_cost = 0
    selected_ids = []
    
    for edge_id, u, v, weight in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_ids.append(edge_id)
    
    return total_cost, selected_ids


def main():
    """Main function to read input and output the result."""
    # Read input from stdin
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    # First two numbers: n (vertices) and m (edges)
    idx = 0
    n = int(data[idx])
    idx += 1
    m = int(data[idx])
    idx += 1
    
    edges = []
    for i in range(m):
        # Each edge: id, u, v, weight
        edge_id = int(data[idx])
        idx += 1
        u = int(data[idx])
        idx += 1
        v = int(data[idx])
        idx += 1
        weight = int(data[idx])
        idx += 1
        edges.append((edge_id, u, v, weight))
    
    # Find the minimum spanning forest
    total_cost, selected_ids = minimum_spanning_forest(n, edges)
    
    # Sort selected IDs for consistent output
    selected_ids.sort()
    
    # Output: total cost on first line, then selected edge IDs
    print(total_cost)
    if selected_ids:
        print(' '.join(map(str, selected_ids)))
    else:
        print()  # Empty line if no edges selected


if __name__ == "__main__":
    main()