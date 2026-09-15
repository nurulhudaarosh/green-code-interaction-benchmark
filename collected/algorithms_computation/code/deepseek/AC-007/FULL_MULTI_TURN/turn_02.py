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
    """
    if n <= 0:
        return 0, []
    
    # Create list of (weight, u, v, edge_id) and sort
    # Sort by weight primarily, then by edge_id for deterministic tie-breaking
    sorted_edges = []
    for edge_id, (u, v, weight) in enumerate(edges):
        sorted_edges.append((weight, u, v, edge_id))
    
    # Key: sort by weight, then by edge ID (as required)
    sorted_edges.sort(key=lambda x: (x[0], x[3]))
    
    dsu = DSU(n)
    total_cost = 0
    selected_edges = []
    
    for weight, u, v, edge_id in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edges.append(edge_id)
    
    # Return edge IDs in ascending order as required
    return total_cost, sorted(selected_edges)


def parse_input() -> Tuple[int, List[Tuple[int, int, int]]]:
    """Parse input from stdin."""
    data = sys.stdin.read().strip().split()
    if not data:
        return 0, []
    
    # First two values: n and m
    n = int(data[0])
    m = int(data[1])
    
    edges = []
    idx = 2
    for _ in range(m):
        u = int(data[idx])
        v = int(data[idx + 1])
        w = int(data[idx + 2])
        edges.append((u, v, w))
        idx += 3
    
    return n, edges


def main():
    """Main entry point."""
    n, edges = parse_input()
    
    if n == 0:
        print(0)
        print()
        return
    
    total_cost, selected_ids = minimum_spanning_forest(n, edges)
    
    # Output format
    print(total_cost)
    if selected_ids:
        print(" ".join(map(str, selected_ids)))
    else:
        print()  # Empty second line when no edges selected


if __name__ == "__main__":
    main()