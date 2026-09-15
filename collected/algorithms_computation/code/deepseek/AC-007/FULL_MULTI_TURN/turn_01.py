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
        """
        Union the sets containing x and y.
        Returns True if they were merged, False if they were already connected.
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        
        # Union by rank
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1
        
        return True


def minimum_spanning_forest(
    n: int,
    edges: List[Tuple[int, int, int]]
) -> Tuple[int, List[int]]:
    """
    Given an undirected weighted graph with n vertices (0 to n-1) and a list of edges
    where each edge is (u, v, weight), return the total cost and selected edge IDs
    of the minimum spanning forest.
    
    Edge IDs are determined by their position in the input list (0-indexed).
    Equal-cost edges are processed in increasing original ID order.
    
    Args:
        n: Number of vertices
        edges: List of edges as (u, v, weight)
    
    Returns:
        Tuple of (total_cost, selected_edge_ids)
    """
    if n <= 0:
        return 0, []
    
    # Create list of (weight, u, v, edge_id)
    # Sort by weight first, then by edge_id for deterministic tie-breaking
    sorted_edges = [(weight, u, v, idx) for idx, (u, v, weight) in enumerate(edges)]
    sorted_edges.sort(key=lambda x: (x[0], x[3]))  # Sort by weight, then by ID
    
    dsu = DSU(n)
    total_cost = 0
    selected_edges = []
    
    for weight, u, v, edge_id in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edges.append(edge_id)
    
    return total_cost, sorted(selected_edges)  # Return in ascending order


def parse_input() -> Tuple[int, List[Tuple[int, int, int]]]:
    """
    Parse input from stdin.
    First line: n m (vertices and edges)
    Next m lines: u v w (edge from u to v with weight w)
    """
    data = sys.stdin.read().strip().split()
    if not data:
        return 0, []
    
    it = iter(data)
    n = int(next(it))
    m = int(next(it))
    
    edges = []
    for _ in range(m):
        u = int(next(it))
        v = int(next(it))
        w = int(next(it))
        edges.append((u, v, w))
    
    return n, edges


def main():
    """Main entry point."""
    n, edges = parse_input()
    total_cost, selected_edge_ids = minimum_spanning_forest(n, edges)
    
    # Output format: total_cost on first line, edge IDs on second line
    print(total_cost)
    if selected_edge_ids:
        print(" ".join(map(str, selected_edge_ids)))
    else:
        print()  # Empty line if no edges selected


if __name__ == "__main__":
    main()