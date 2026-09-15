class DisjointSetUnion:
    """Disjoint-Set Union (DSU) / Union-Find with path compression and rank optimization."""
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i != root_j:
            # Union by rank
            if self.rank[root_i] < self.rank[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            if self.rank[root_i] == self.rank[root_j]:
                self.rank[root_i] += 1
            return True
        return False


def minimum_spanning_forest(num_vertices: int, edges: list[tuple[int, int, float]]) -> tuple[float, list[int]]:
    """
    Computes the Minimum Spanning Forest using Kruskal's Algorithm.

    Handles boundary conditions: V=0, V=1, E=0, self-loops, negative/zero weights,
    multi-edges, and disconnected components.
    """
    if num_vertices <= 0:
        return 0, []

    # Filter out invalid vertex references and self-loops early
    indexed_edges = []
    for idx, (u, v, weight) in enumerate(edges):
        # Ignore self-loops and out-of-bound vertex indices
        if 0 <= u < num_vertices and 0 <= v < num_vertices and u != v:
            indexed_edges.append((weight, idx, u, v))

    # Deterministic sort: Primary by weight (asc), Secondary by original edge ID (asc)
    indexed_edges.sort(key=lambda x: (x[0], x[1]))

    dsu = DisjointSetUnion(num_vertices)
    total_cost = 0
    selected_edge_ids = []

    for weight, original_id, u, v in indexed_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(original_id)

    selected_edge_ids.sort()
    return total_cost, selected_edge_ids


# ---------------------------------------------------------
# Test Suite Covering Boundary Cases & Difficult Scenarios
# ---------------------------------------------------------

def run_tests():
    # Test 1: Empty Graph (V=0)
    assert minimum_spanning_forest(0, []) == (0, [])

    # Test 2: Single Vertex, No Edges (V=1, E=0)
    assert minimum_spanning_forest(1, []) == (0, [])

    # Test 3: Multiple Disconnected Singletons (V=5, E=0)
    assert minimum_spanning_forest(5, []) == (0, [])

    # Test 4: Self-loops and Multi-edges
    edges = [
        (0, 0, 10),  # ID 0: Self loop (ignored)
        (0, 1, 5),   # ID 1: Weight 5
        (0, 1, 3),   # ID 2: Parallel edge, weight 3 (chosen)
    ]
    assert minimum_spanning_forest(2, edges) == (3, [2])

    # Test 5: Negative & Zero Weights
    edges = [
        (0, 1, -5),  # ID 0
        (1, 2, 0),   # ID 1
        (2, 0, -2),  # ID 2 (Forms cycle with 0, 1)
    ]
    # Spanning tree selects (-5) and (-2), total = -7, IDs = [0, 2]
    assert minimum_spanning_forest(3, edges) == (-7, [0, 2])

    # Test 6: Tie-Breaking with Equal Weights
    # Triangle 0-1-2 with all edge weights = 4
    edges = [
        (0, 1, 4),  # ID 0
        (1, 2, 4),  # ID 1
        (2, 0, 4),  # ID 2
    ]
    # Must select smallest IDs [0, 1]
    assert minimum_spanning_forest(3, edges) == (8, [0, 1])

    # Test 7: Fully Disconnected Components (2 Separate Subtrees)
    # Comp A: 0-1 (w=2), Comp B: 2-3 (w=3)
    edges = [
        (0, 1, 2),  # ID 0
        (2, 3, 3),  # ID 1
    ]
    assert minimum_spanning_forest(4, edges) == (5, [0, 1])

    print("All boundary and unit tests passed successfully!")


if __name__ == "__main__":
    run_tests()