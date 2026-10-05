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
            # Union by size
            if self.size[root_i] < self.size[root_j]:
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
    Process edge weight threshold queries offline using DSU.

    :param n: Number of vertices (0 to n-1)
    :param edges: List of tuples (u, v, weight)
    :param queries: List of query thresholds q
    :return: List of tuples (num_components, max_component_size) for each query
    """
    if n == 0:
        return [(0, 0)] * len(queries)

    # Sort edges by weight ascending
    sorted_edges = sorted(edges, key=lambda e: e[2])

    # Pair queries with original index and sort by threshold ascending
    indexed_queries = sorted(enumerate(queries), key=lambda x: x[1])

    results = [None] * len(queries)
    dsu = DisjointSetUnion(n)
    edge_idx = 0
    num_edges = len(sorted_edges)

    for original_idx, q in indexed_queries:
        # Add all edges with weight <= q
        while edge_idx < num_edges and sorted_edges[edge_idx][2] <= q:
            u, v, _ = sorted_edges[edge_idx]
            dsu.union(u, v)
            edge_idx += 1

        results[original_idx] = (dsu.num_components, dsu.max_component_size)

    return results


# --- Example Usage ---
if __name__ == "__main__":
    N = 5
    edges = [
        (0, 1, 2),
        (1, 2, 5),
        (2, 3, 1),
        (3, 4, 4),
        (0, 4, 7)
    ]
    queries = [0, 2, 4, 6]

    answers = process_threshold_queries(N, edges, queries)
    for q, ans in zip(queries, answers):
        print(f"Threshold q = {q}: Components = {ans[0]}, Largest Size = {ans[1]}")