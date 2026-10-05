class DisjointSetUnion:
    """Disjoint Set Union (DSU) tracking component count and max size."""
    def __init__(self, n: int):
        self.n = n
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_component_size = 1 if n > 0 else 0

    def find(self, i: int) -> int:
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])  # Path compression
        return self.parent[i]

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i != root_j:
            # Union by size; tie-break deterministically by root index
            if self.size[root_i] < self.size[root_j] or (
                self.size[root_i] == self.size[root_j] and root_i > root_j
            ):
                root_i, root_j = root_j, root_i
            
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            
            self.num_components -= 1
            if self.size[root_i] > self.max_component_size:
                self.max_component_size = self.size[root_i]
            return True
        return False


def query_components_by_threshold(n: int, edges: list[tuple[int, int, int]], queries: list[int]) -> list[tuple[int, int]]:
    """
    Evaluates graph components for each weight threshold query.
    
    :param n: Number of vertices (0 to n-1)
    :param edges: List of tuples (u, v, weight)
    :param queries: List of query thresholds q
    :return: List of tuples (num_components, max_component_size)
    """
    # Boundary case: Empty graph
    if n <= 0:
        return [(0, 0)] * len(queries)
    
    # Preserve original indices for stable/deterministic sorting on equal edge weights
    indexed_edges = sorted(enumerate(edges), key=lambda item: (item[1][2], item[0]))
    
    # Sort queries while keeping track of original output order
    indexed_queries = sorted(enumerate(queries), key=lambda item: (item[1], item[0]))
    
    dsu = DisjointSetUnion(n)
    results = [(0, 0)] * len(queries)
    
    edge_idx = 0
    num_edges = len(indexed_edges)

    for orig_q_idx, threshold in indexed_queries:
        while edge_idx < num_edges and indexed_edges[edge_idx][1][2] <= threshold:
            _, (u, v, w) = indexed_edges[edge_idx]
            # Verify boundary check for vertex indices
            if 0 <= u < n and 0 <= v < n:
                dsu.union(u, v)
            edge_idx += 1
        
        results[orig_q_idx] = (dsu.num_components, dsu.max_component_size)

    return results


# --- Test Suite ---

def run_tests():
    # Test 1: Empty graph / zero vertices
    assert query_components_by_threshold(0, [(0, 1, 5)], [0, 5, 10]) == [(0, 0), (0, 0), (0, 0)]

    # Test 2: Single vertex with self-loop
    assert query_components_by_threshold(1, [(0, 0, 2)], [-1, 2, 5]) == [(1, 1), (1, 1), (1, 1)]

    # Test 3: No edges
    assert query_components_by_threshold(4, [], [0, 100]) == [(4, 1), (4, 1)]

    # Test 4: Threshold lower than all weights and higher than all weights
    edges_4 = [(0, 1, 10), (1, 2, 20)]
    assert query_components_by_threshold(3, edges_4, [0, 5, 10, 15, 20, 25]) == [
        (3, 1), # q=0: no edges
        (3, 1), # q=5: no edges
        (2, 2), # q=10: edge (0,1) added -> comps={0,1}, {2}
        (2, 2), # q=15: edge (0,1) added
        (1, 3), # q=20: both edges added -> full graph connected
        (1, 3)  # q=25: full graph connected
    ]

    # Test 5: Duplicate weights, parallel edges, self-loops
    edges_5 = [
        (0, 1, 5),
        (0, 1, 5), # parallel edge
        (2, 2, 5), # self-loop
        (2, 3, 5),
    ]
    # At q=5, edges (0,1) and (2,3) create two components of size 2. Total comps = 2, max size = 2
    assert query_components_by_threshold(4, edges_5, [4, 5]) == [(4, 1), (2, 2)]

    # Test 6: Unsorted queries order preservation
    edges_6 = [(0, 1, 3), (1, 2, 7)]
    queries_6 = [10, 0, 5]
    assert query_components_by_threshold(3, edges_6, queries_6) == [(1, 3), (3, 1), (2, 2)]

    print("All boundary tests passed successfully!")

if __name__ == "__main__":
    run_tests()