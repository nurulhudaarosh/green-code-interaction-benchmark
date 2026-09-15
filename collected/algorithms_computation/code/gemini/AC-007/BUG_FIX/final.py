class DSU:
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


def minimum_spanning_forest(
    num_vertices: int, edges: list[tuple[int, int, float | int]]
) -> tuple[float | int, list[int]]:
    """
    Computes the Minimum Spanning Forest using Kruskal's algorithm.

    Strict Tie-Breaking Rule: Equal-weight edges are prioritized 
    strictly by original edge ID in ascending order.
    """
    # Store edges as (edge_id, u, v, weight)
    decorated_edges = [
        (edge_id, u, v, weight) for edge_id, (u, v, weight) in enumerate(edges)
    ]

    # Explicitly sort ONLY by (weight, edge_id) to prevent endpoint comparison leakage
    decorated_edges.sort(key=lambda item: (item[3], item[0]))

    dsu = DSU(num_vertices)
    total_cost = 0
    selected_edge_ids = []

    for edge_id, u, v, weight in decorated_edges:
        if dsu.union(u, v):
            total_cost += weight
            selected_edge_ids.append(edge_id)

    return total_cost, selected_edge_ids


# Verification of the fix on the counterexample
if __name__ == "__main__":
    edges = [
        (1, 0, 10),  # Edge ID 0
        (0, 1, 10),  # Edge ID 1
    ]
    cost, selected_ids = minimum_spanning_forest(2, edges)
    print(f"Total Cost: {cost}")
    print(f"Selected Edge IDs: {selected_ids}")  # Strictly outputs [0]