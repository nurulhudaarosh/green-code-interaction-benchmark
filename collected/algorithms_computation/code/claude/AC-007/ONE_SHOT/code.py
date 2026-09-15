class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def minimum_spanning_forest(num_vertices, edges):
    """
    edges: list of tuples (edge_id, u, v, weight)
    Returns: (total_cost, sorted_list_of_selected_edge_ids)
    """
    # Deterministic ordering: by weight, then by original edge ID
    sorted_edges = sorted(edges, key=lambda e: (e[3], e[0]))

    dsu = DSU(num_vertices)
    total_cost = 0
    selected_ids = []

    for edge_id, u, v, weight in sorted_edges:
        if u == v:
            continue  # self-loop never belongs in a forest
        if dsu.union(u, v):
            total_cost += weight
            selected_ids.append(edge_id)

    selected_ids.sort()
    return total_cost, selected_ids


if __name__ == "__main__":
    # vertices 0..5, edges = (id, u, v, weight)
    edges = [
        (1, 0, 1, 4),
        (2, 0, 2, 4),
        (3, 1, 2, 2),
        (4, 1, 0, 4),
        (5, 2, 3, 3),
        (6, 3, 4, 2),
        (7, 4, 5, 6),
        (8, 5, 3, 6),
    ]
    cost, ids = minimum_spanning_forest(6, edges)
    print("Total cost:", cost)
    print("Selected edge IDs:", ids)