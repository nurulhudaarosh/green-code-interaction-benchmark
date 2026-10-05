"""
Threshold Connectivity Tracker

Problem Restatement:
For an undirected weighted graph with n vertices and m edges, answer each
threshold query q as follows:

    - Consider only edges whose weight <= q.
    - Determine the number of connected components.
    - Determine the size of the largest connected component.

Each query is answered independently in terms of the threshold value, but
all queries are processed efficiently using one incremental DSU structure.

Key Constraints / Assumptions:
- The graph is undirected.
- Vertices are numbered 0 through n - 1.
- Edge weights and query thresholds are comparable numeric values.
- Every vertex exists even if it has no incident edge.
- Edges with weight exactly equal to q are included.
- Queries may be repeated or given in any order.
- The answer must be deterministic.
- No randomness, network access, APIs, external services, or human input
  during execution.
- Standard library only.

Required Output:
For every query q, return:
    (number_of_connected_components, largest_component_size)

The answers must be returned in the same order as the original queries.

Algorithm:
1. Sort all edges by weight.
2. Sort queries by threshold while remembering their original indices.
3. Start with every vertex in its own connected component.
4. Process queries from smallest threshold to largest.
5. Before answering a query q, union every edge with weight <= q.
6. Maintain:
       - component_count
       - largest_component_size
   inside a Disjoint Set Union (DSU / Union-Find).
7. Store each answer at the query's original index.

Complexity:
- Sorting edges: O(m log m)
- Sorting queries: O(k log k)
- DSU operations: O((m + k) * alpha(n)) approximately
- Overall: O(m log m + k log k)
- Space: O(n + m + k)
"""

from typing import List, Tuple


class DSU:
    """Deterministic Disjoint Set Union with component-size tracking."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        """Return the representative of x using path compression."""
        root = x

        while self.parent[root] != root:
            root = self.parent[root]

        while self.parent[x] != x:
            next_x = self.parent[x]
            self.parent[x] = root
            x = next_x

        return root

    def union(self, a: int, b: int) -> bool:
        """
        Merge the components containing a and b.

        Returns True if two different components were merged.
        Uses deterministic union-by-size; ties are resolved by the
        smaller representative index.
        """
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

        # Larger component becomes the parent.
        # If sizes are equal, smaller root becomes the parent.
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a
        elif (
            self.size[root_a] == self.size[root_b]
            and root_a > root_b
        ):
            root_a, root_b = root_b, root_a

        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]

        return True

    def component_size(self, x: int) -> int:
        """Return the size of x's current connected component."""
        return self.size[self.find(x)]


def threshold_connectivity(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
) -> List[Tuple[int, int]]:
    """
    Answer threshold connectivity queries.

    Parameters
    ----------
    n:
        Number of vertices, numbered 0 through n - 1.

    edges:
        List of weighted undirected edges:
            (u, v, weight)

    queries:
        Threshold values q.

    Returns
    -------
    List[Tuple[int, int]]
        For each query q, in original query order:
            (number_of_components, largest_component_size)

    Notes
    -----
    An edge (u, v, w) is active for threshold q exactly when w <= q.
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    # Validate vertices.
    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge contains a vertex outside 0..n-1")

    # Every vertex initially forms its own component.
    dsu = DSU(n)

    component_count = n
    largest_component_size = 1 if n > 0 else 0

    # Include original edge position as a deterministic final tie-breaker.
    sorted_edges = sorted(
        enumerate(edges),
        key=lambda item: (item[1][2], item[0]),
    )

    # Keep original query positions so answers are restored to input order.
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0]),
    )

    answers = [None] * len(queries)
    edge_index = 0

    for query_index, threshold in sorted_queries:
        # Activate every edge with weight <= threshold.
        while (
            edge_index < len(sorted_edges)
            and sorted_edges[edge_index][1][2] <= threshold
        ):
            _, (u, v, _) = sorted_edges[edge_index]

            if dsu.union(u, v):
                component_count -= 1

                root = dsu.find(u)
                if dsu.size[root] > largest_component_size:
                    largest_component_size = dsu.size[root]

            edge_index += 1

        answers[query_index] = (
            component_count,
            largest_component_size,
        )

    return answers


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:
    # Test 1: Basic example.
    #
    # At q=0:
    #   No edges are active -> 4 components, largest size 1.
    #
    # At q=2:
    #   0-1 and 1-2 are active -> 2 components, largest size 3.
    #
    # At q=3:
    #   2-3 becomes active -> 1 component, largest size 4.
    n = 4
    edges = [
        (0, 1, 1),
        (1, 2, 2),
        (2, 3, 3),
    ]
    queries = [0, 2, 3]

    assert threshold_connectivity(n, edges, queries) == [
        (4, 1),
        (2, 3),
        (1, 4),
    ]

    # Test 2: Queries are not sorted.
    queries = [3, 0, 2]

    assert threshold_connectivity(n, edges, queries) == [
        (1, 4),
        (4, 1),
        (2, 3),
    ]

    # Test 3: Repeated queries must return identical results.
    queries = [2, 2, 1, 2]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 3),
        (2, 3),
        (3, 2),
        (2, 3),
    ]

    # Test 4: Equal edge weights.
    # Both edges with weight 5 must be active at q=5.
    n = 4
    edges = [
        (0, 1, 5),
        (2, 3, 5),
    ]
    queries = [4, 5]

    assert threshold_connectivity(n, edges, queries) == [
        (4, 1),
        (2, 2),
    ]

    # Test 5: Disconnected graph and isolated vertices.
    n = 6
    edges = [
        (0, 1, 10),
        (1, 2, 20),
        (3, 4, 5),
    ]
    queries = [0, 5, 10, 20]

    assert threshold_connectivity(n, edges, queries) == [
        (6, 1),
        (5, 2),
        (4, 2),
        (3, 3),
    ]

    # Test 6: Empty graph.
    n = 5
    edges = []
    queries = [-1, 0, 100]

    assert threshold_connectivity(n, edges, queries) == [
        (5, 1),
        (5, 1),
        (5, 1),
    ]

    # Test 7: Empty query list.
    assert threshold_connectivity(5, [(0, 1, 1)], []) == []

    # Test 8: Smallest permitted graph.
    # One vertex with no edges.
    assert threshold_connectivity(1, [], [-100, 0, 100]) == [
        (1, 1),
        (1, 1),
        (1, 1),
    ]

    # Test 9: Single vertex with a self-loop.
    # A self-loop does not reduce the component count.
    assert threshold_connectivity(1, [(0, 0, 7)], [6, 7]) == [
        (1, 1),
        (1, 1),
    ]

    # Test 10: Negative edge weights and thresholds.
    n = 3
    edges = [
        (0, 1, -10),
        (1, 2, -5),
    ]
    queries = [-11, -10, -5]

    assert threshold_connectivity(n, edges, queries) == [
        (3, 1),
        (2, 2),
        (1, 3),
    ]

    # Test 11: Cycles must not incorrectly reduce component count.
    n = 4
    edges = [
        (0, 1, 1),
        (1, 2, 2),
        (2, 0, 3),
        (2, 3, 4),
    ]
    queries = [2, 3, 4]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 3),
        (2, 3),
        (1, 4),
    ]

    # Test 12: Very large integer weights/thresholds.
    # Python integers handle these values deterministically.
    LIMIT = 10**18
    n = 3
    edges = [
        (0, 1, -LIMIT),
        (1, 2, LIMIT),
    ]
    queries = [-LIMIT, 0, LIMIT]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 2),
        (2, 2),
        (1, 3),
    ]

    # Test 13: Large threshold includes every edge.
    n = 5
    edges = [
        (0, 1, 1),
        (1, 2, 2),
        (3, 4, 3),
    ]

    assert threshold_connectivity(n, edges, [10**18]) == [
        (2, 3),
    ]

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()