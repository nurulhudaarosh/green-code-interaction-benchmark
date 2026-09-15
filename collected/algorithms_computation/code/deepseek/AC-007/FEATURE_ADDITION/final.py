import sys
from typing import List, Tuple, Optional, Dict, Any

class DisjointSetUnion:
    """
    Disjoint Set Union (Union-Find) data structure with path compression
    and union by rank.
    """
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.union_count = 0  # Track successful unions

    def find(self, x: int) -> int:
        """Finds the representative (root) of the set containing x."""
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # Path compression
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        """
        Unites the sets containing x and y.
        Returns True if they were in different sets (successful union),
        otherwise False.
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
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

        self.union_count += 1
        return True


def kruskal_minimum_spanning_forest(
    n: int, 
    edges: List[Tuple[int, int, int]],
    return_summary: bool = False
) -> Tuple[int, List[int], Optional[Dict[str, Any]]]:
    """
    Finds the Minimum Spanning Forest (MSF) of an undirected weighted graph
    using Kruskal's algorithm.

    Args:
        n: Number of vertices (0 to n-1).
        edges: List of edges as (u, v, weight) where u and v are 0-based vertex indices.
        return_summary: If True, returns an additional operation_summary dict.

    Returns:
        - If return_summary is False: (total_cost, selected_edge_ids)
        - If return_summary is True: (total_cost, selected_edge_ids, operation_summary)
        
        Where:
        - total_cost is the sum of weights of edges in the MSF.
        - selected_edge_ids is a list of original edge indices (0-based) selected for the MSF.
        - operation_summary is a dictionary containing deterministic computational statistics.
    """
    # Initialize summary counters
    summary = {
        'total_edges_considered': 0,
        'successful_unions': 0,
        'failed_unions': 0,
        'total_comparisons': 0,  # Number of find operations (each union does 2 finds)
        'sorting_complexity': 0,  # n log n approximation
        'vertices_count': n,
        'edges_count': len(edges)
    } if return_summary else None

    # If there are no vertices, return early
    if n <= 0:
        if return_summary:
            return 0, [], summary
        return 0, []

    # Create list of tuples (weight, u, v, original_id) for sorting
    edge_list = [(w, u, v, idx) for idx, (u, v, w) in enumerate(edges)]

    # Sort edges by weight, then by original ID (deterministic tie-breaking)
    edge_list.sort(key=lambda x: (x[0], x[3]))

    # Track sorting complexity for summary
    if return_summary and len(edge_list) > 1:
        # Approximate sorting comparisons: n * log2(n)
        import math
        summary['sorting_complexity'] = int(len(edge_list) * math.log2(len(edge_list))) + 1

    dsu = DisjointSetUnion(n)
    total_cost = 0
    selected_ids = []

    for w, u, v, original_id in edge_list:
        if return_summary:
            summary['total_edges_considered'] += 1
            # Each union attempt does 2 find operations
            summary['total_comparisons'] += 2

        # Attempt to union
        if dsu.union(u, v):
            total_cost += w
            selected_ids.append(original_id)
            if return_summary:
                summary['successful_unions'] += 1
        else:
            if return_summary:
                summary['failed_unions'] += 1

    if return_summary:
        return total_cost, selected_ids, summary
    
    return total_cost, selected_ids


def main() -> None:
    """
    Reads input from stdin and outputs the total cost and selected edge IDs.
    Input format:
        First line: two integers n and m (number of vertices and edges).
        Next m lines: three integers u, v, w (edge between u and v with weight w).
    Output format:
        First line: total cost of the Minimum Spanning Forest.
        Second line: space-separated original edge IDs (0-based) in the order they were selected.
    """
    data = sys.stdin.read().strip().split()
    if not data:
        return

    it = iter(data)
    try:
        n = int(next(it))
        m = int(next(it))
    except StopIteration:
        return

    edges = []
    for idx in range(m):
        try:
            u = int(next(it))
            v = int(next(it))
            w = int(next(it))
        except StopIteration:
            break
        edges.append((u, v, w))

    # Call the function without summary (original behavior)
    total_cost, selected_ids = kruskal_minimum_spanning_forest(n, edges, return_summary=False)

    # Print total cost
    print(total_cost)
    # Print selected edge IDs (if any), space-separated
    if selected_ids:
        print(' '.join(map(str, selected_ids)))
    else:
        print()  # Empty line for no selected edges


if __name__ == "__main__":
    main()