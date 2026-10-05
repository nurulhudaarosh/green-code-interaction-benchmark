# Threshold Connectivity Tracker
#
# Problem:
# For each weight threshold q, consider only graph edges whose weight <= q.
# Return:
#   1. The number of connected components.
#   2. The size of the largest connected component.
#
# Key constraints:
# - The graph is undirected.
# - Vertices are identified by indices 0..n-1.
# - Each edge is (u, v, weight).
# - Each query is a threshold q.
# - An edge is active exactly when weight <= q.
# - Queries must be answered deterministically in their original order.
# - Only the Python standard library is used.
#
# Required output:
# For every query q, return:
#     (number_of_components, largest_component_size)
# in the same order as the input queries.
#
# Algorithm:
# 1. Sort edges by weight.
# 2. Sort queries by threshold while keeping their original indices.
# 3. Start with every vertex in its own component.
# 4. For each query, union every edge whose weight <= q.
# 5. Maintain:
#      - component_count
#      - largest_component_size
#    incrementally, so each query is answered efficiently.
# 6. Store each answer at its original query index.
#
# Time complexity:
#   Sorting: O(E log E + Q log Q)
#   DSU operations: O(E alpha(V))
#   Total: O(E log E + Q log Q + E alpha(V))
#
# Space complexity:
#   O(V + E + Q)


from typing import List, Tuple


Edge = Tuple[int, int, int]
Answer = Tuple[int, int]


class DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = 1 if n > 0 else 0

    def find(self, x: int) -> int:
        # Path compression.
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return False

        # Union by size gives deterministic behavior without
        # changing the required component results.
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra

        self.parent[rb] = ra
        self.size[ra] += self.size[rb]

        self.components -= 1
        if self.size[ra] > self.largest:
            self.largest = self.size[ra]

        return True


def threshold_connectivity(
    n: int,
    edges: List[Edge],
    queries: List[int],
) -> List[Answer]:
    """
    Return (component_count, largest_component_size) for every
    threshold query, preserving the original query order.

    Parameters:
        n:
            Number of vertices, indexed 0 through n-1.

        edges:
            List of undirected edges:
            (u, v, weight)

        queries:
            Threshold values.

    Returns:
        A list where result[i] corresponds to queries[i].
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge vertex is outside the valid range")

    # Sort by threshold, then by original index for deterministic
    # processing when thresholds are equal.
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0]),
    )

    # Sort edges by weight.  Original position is included to make
    # ordering deterministic when edge weights are equal.
    sorted_edges = sorted(
        enumerate(edges),
        key=lambda item: (item[1][2], item[0]),
    )

    dsu = DSU(n)
    answers: List[Answer] = [None] * len(queries)  # type: ignore

    edge_index = 0

    for query_index, threshold in sorted_queries:
        # Activate every edge with weight <= threshold.
        while (
            edge_index < len(sorted_edges)
            and sorted_edges[edge_index][1][2] <= threshold
        ):
            _, (u, v, _) = sorted_edges[edge_index]
            dsu.union(u, v)
            edge_index += 1

        answers[query_index] = (
            dsu.components,
            dsu.largest,
        )

    return answers


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:
    # Test 1: Basic increasing thresholds.
    n = 4
    edges = [
        (0, 1, 2),
        (1, 2, 5),
        (2, 3, 8),
    ]
    queries = [0, 2, 5, 8]

    assert threshold_connectivity(n, edges, queries) == [
        (4, 1),
        (3, 2),
        (2, 3),
        (1, 4),
    ]

    # Test 2: Queries are not sorted.
    queries = [5, 0, 8, 2]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 3),
        (4, 1),
        (1, 4),
        (3, 2),
    ]

    # Test 3: Equal thresholds.
    queries = [5, 5, 5]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 3),
        (2, 3),
        (2, 3),
    ]

    # Test 4: Repeated edges and cycles.
    n = 4
    edges = [
        (0, 1, 1),
        (1, 2, 1),
        (0, 2, 1),
        (2, 3, 3),
        (0, 3, 4),
    ]
    queries = [1, 2, 3, 4]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 3),
        (2, 3),
        (1, 4),
        (1, 4),
    ]

    # Test 5: No edges.
    assert threshold_connectivity(3, [], [-10, 0, 100]) == [
        (3, 1),
        (3, 1),
        (3, 1),
    ]

    # Test 6: Single vertex.
    assert threshold_connectivity(1, [], [-5, 0, 10]) == [
        (1, 1),
        (1, 1),
        (1, 1),
    ]

    # Test 7: Empty graph.
    assert threshold_connectivity(0, [], [-1, 0, 1]) == [
        (0, 0),
        (0, 0),
        (0, 0),
    ]

    # Test 8: Negative edge weights and thresholds.
    n = 3
    edges = [
        (0, 1, -5),
        (1, 2, 2),
    ]
    queries = [-10, -5, 0, 2]

    assert threshold_connectivity(n, edges, queries) == [
        (3, 1),
        (2, 2),
        (2, 2),
        (1, 3),
    ]

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()