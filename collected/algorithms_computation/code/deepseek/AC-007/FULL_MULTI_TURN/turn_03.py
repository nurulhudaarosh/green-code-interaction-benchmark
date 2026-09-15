import sys
from typing import List, Tuple, Dict, Any

class DSU:
    """Disjoint Set Union (Union-Find) with path compression and union by rank."""
    
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.find_count = 0  # Track number of find operations
    
    def find(self, x: int) -> int:
        """Find the root with path compression."""
        self.find_count += 1
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
    edges: List[Tuple[int, int, int]],
    include_summary: bool = False
) -> Tuple[int, List[int]] | Tuple[int, List[int], Dict[str, Any]]:
    """
    Compute minimum spanning forest using Kruskal's algorithm.
    
    Args:
        n: Number of vertices (0 to n-1)
        edges: List of (u, v, weight) tuples
        include_summary: If True, include operation summary in return
        
    Returns:
        If include_summary is False: (total_cost, list_of_selected_edge_ids)
        If include_summary is True: (total_cost, list_of_selected_edge_ids, operation_summary)
        
        Edge IDs are 0-indexed positions in the input edges list.
        Equal weights are processed by ascending edge ID.
        
        operation_summary contains:
            - edges_sorted: number of edges sorted
            - successful_unions: number of edges added to forest
            - failed_unions: number of edges that formed cycles
            - total_find_operations: total DSU find operations performed
            - total_union_attempts: total edges processed (successful + failed)
    """
    if n <= 0:
        if include_summary:
            return 0, [], {
                'edges_sorted': 0,
                'successful_unions': 0,
                'failed_unions': 0,
                'total_find_operations': 0,
                'total_union_attempts': 0
            }
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
    successful_unions = 0
    failed_unions = 0
    
    for weight, u, v, edge_id in sorted_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edges.append(edge_id)
            successful_unions += 1
        else:
            failed_unions += 1
    
    # Return edge IDs in ascending order as required
    selected_edges_sorted = sorted(selected_edges)
    
    if include_summary:
        operation_summary = {
            'edges_sorted': len(sorted_edges),
            'successful_unions': successful_unions,
            'failed_unions': failed_unions,
            'total_find_operations': dsu.find_count,
            'total_union_attempts': successful_unions + failed_unions
        }
        return total_cost, selected_edges_sorted, operation_summary
    
    return total_cost, selected_edges_sorted


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
    """Main entry point with optional summary output."""
    n, edges = parse_input()
    
    if n == 0:
        print(0)
        print()
        # Print summary if requested via command line argument
        if len(sys.argv) > 1 and sys.argv[1] == '--summary':
            print("Operation Summary:")
            print("  edges_sorted: 0")
            print("  successful_unions: 0")
            print("  failed_unions: 0")
            print("  total_find_operations: 0")
            print("  total_union_attempts: 0")
        return
    
    # Check if summary is requested via command line argument
    include_summary = len(sys.argv) > 1 and sys.argv[1] == '--summary'
    
    if include_summary:
        total_cost, selected_ids, summary = minimum_spanning_forest(n, edges, include_summary=True)
        
        # Original output format (unchanged)
        print(total_cost)
        if selected_ids:
            print(" ".join(map(str, selected_ids)))
        else:
            print()
        
        # Additional summary output (new feature)
        print("Operation Summary:")
        print(f"  edges_sorted: {summary['edges_sorted']}")
        print(f"  successful_unions: {summary['successful_unions']}")
        print(f"  failed_unions: {summary['failed_unions']}")
        print(f"  total_find_operations: {summary['total_find_operations']}")
        print(f"  total_union_attempts: {summary['total_union_attempts']}")
    else:
        total_cost, selected_ids = minimum_spanning_forest(n, edges, include_summary=False)
        
        # Original output format (unchanged)
        print(total_cost)
        if selected_ids:
            print(" ".join(map(str, selected_ids)))
        else:
            print()


if __name__ == "__main__":
    main()