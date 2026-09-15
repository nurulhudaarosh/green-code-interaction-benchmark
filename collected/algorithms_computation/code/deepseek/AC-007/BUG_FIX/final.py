import sys
from typing import List, Tuple


class DSU:
    """Disjoint Set Union with path compression and union by rank."""
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
    
    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


def minimum_spanning_forest(n: int, edges: List[Tuple[int, int, int, int]]) -> Tuple[int, List[int]]:
    """
    Find MSF using Kruskal's algorithm with deterministic tie-breaking by original ID.
    
    Args:
        n: Number of vertices (0 to n-1)
        edges: List of (u, v, weight, edge_id)
        
    Returns:
        Tuple of (total_cost, selected_edge_ids_in_processing_order)
    """
    if n == 0:
        return 0, []
    
    # CRITICAL: Sort by (weight, edge_id) for deterministic tie-breaking
    # This ensures equal-weight edges are processed by original ID ascending
    sorted_edges = sorted(edges, key=lambda x: (x[2], x[3]))
    
    dsu = DSU(n)
    total_cost = 0
    selected_ids = []  # Preserve processing order
    
    for u, v, weight, edge_id in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_ids.append(edge_id)  # Keep in order of addition
    
    return total_cost, selected_ids


def solve() -> None:
    """Read from stdin and output results."""
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
    
    # Output: total cost on first line, selected IDs on second line
    # IDs are output in the order they were processed/selected
    print(total_cost)
    if selected_ids:
        print(' '.join(map(str, selected_ids)))
    else:
        print()  # Empty line for no edges


if __name__ == "__main__":
    solve()