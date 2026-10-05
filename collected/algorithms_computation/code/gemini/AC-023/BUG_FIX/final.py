class DisjointSetUnion:
    def __init__(self, n: int):
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
            # Deterministic union by size, tie-broken by smaller root index
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            elif self.size[root_i] == self.size[root_j] and root_i > root_j:
                root_i, root_j = root_j, root_i

            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]

            # Update global trackers
            self.num_components -= 1
            if self.size[root_i] > self.max_component_size:
                self.max_component_size = self.size[root_i]
            return True
        return False


def process_threshold_queries(n: int, edges: list, queries: list) -> list:
    """
    Process edge weight threshold queries offline using DSU with deterministic tie-handling.

    :param n: Number of vertices (0 to n-1)
    :param edges: List of tuples (u, v, weight)
    :param queries: List of query thresholds q
    :return: List of tuples (num_components, max_component_size) for each query
    """
    if n == 0:
        return [(0, 0)] * len(queries)

    # Normalize edges so u <= v for consistent tie-breaking
    normalized_edges = [(min(u, v), max(u, v), w) for u, v, w in edges]

    # Deterministic edge sorting: primary key weight (w), secondary keys u, v
    sorted_edges = sorted(normalized_edges, key=lambda e: (e[2], e[0], e[1]))

    # Deterministic query sorting: primary key threshold (q), secondary key original_idx
    indexed_queries = sorted(enumerate(queries), key=lambda x: (x[1], x[0]))

    results = [None] * len(queries)
    dsu = DisjointSetUnion(n)
    edge_idx = 0
    num_edges = len(sorted_edges)

    for original_idx, q in indexed_queries:
        # Add all edges with weight <= q deterministically
        while edge_idx < num_edges and sorted_edges[edge_idx][2] <= q:
            u, v, _ = sorted_edges[edge_idx]
            dsu.union(u, v)
            edge_idx += 1

        results[original_idx] = (dsu.num_components, dsu.max_component_size)

    return results


# --- Verification Example ---
if __name__ == "__main__":
    N = 4
    # Edges with tied weights
    edges1 = [(0, 1, 2), (2, 3, 2)]
    edges2 = [(2, 3, 2), (0, 1, 2)]  # Reversed input order
    queries = [2, 1, 2]

    res1 = process_threshold_queries(N, edges1, queries)
    res2 = process_threshold_queries(N, edges2, queries)

    assert res1 == res2, "Execution must be strictly deterministic regardless of edge input order"
    print("Results:", res1)