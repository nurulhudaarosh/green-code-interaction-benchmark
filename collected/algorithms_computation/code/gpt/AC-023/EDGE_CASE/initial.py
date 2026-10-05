# Threshold Connectivity Tracker
#
# Problem:
# For each weight threshold q, consider only graph edges whose weight <= q.
# Return:
#   1. The number of connected components.
#   2. The size of the largest connected component.
#
# Key constraints / requirements:
# - The graph has n vertices and weighted edges (u, v, w).
# - A query threshold q includes every edge with w <= q.
# - Vertices with no active incident edges are still components of size 1.
# - Queries may be given in any order.
# - Results must be returned in the original query order.
# - The algorithm must be deterministic.
# - Edges with equal weights must be processed consistently.
# - Use only the Python standard library.
# - No network, APIs, external services, randomness, or human interaction.
#
# Required output:
# For every query q, return:
#     (number_of_connected_components, largest_component_size)
#
# Algorithm:
# 1. Sort edges by (weight, original_edge_index).
# 2. Sort queries by (threshold, original_query_index).
# 3. Initially, every vertex is its own component:
#       components = n
#       largest_component = 1  (or 0 when n == 0)
# 4. Process queries from smallest threshold to largest.
# 5. Before answering a query q, incrementally add every edge with
#    weight <= q using Union-Find (Disjoint Set Union).
# 6. When two different components are united:
#       components decreases by 1
#       largest_component is updated.
# 7. Store each answer using the query's original index so that the
#    final results match the input query order.
#
# Time complexity:
#   Sorting: O(m log m + k log k)
#   Union-Find operations: O(m alpha(n)) approximately O(m)
#   Total: O(m log m + k log k)
#
# Space complexity:
#   O(n + m + k)
#
# Deterministic tie handling:
# - Edges with equal weights are ordered by their original input index.
# - Queries with equal thresholds are ordered by their original query index.
# - Equal-threshold queries therefore receive identical graph-state results.


from typing import List, Tuple


def threshold_connectivity(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
) -> List[Tuple[int, int]]:
    """
    Return (number_of_components, largest_component_size) for each
    threshold in queries, preserving the original query order.

    Vertices are numbered 0 through n - 1.

    Each edge is (u, v, weight).
    Only edges with weight <= query_threshold are active.

    Raises:
        ValueError: if vertex indices are invalid.
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    # Validate edge endpoints.
    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge contains an invalid vertex index")

    # Empty graph: there are no connected components.
    if n == 0:
        return [(0, 0) for _ in queries]

    # Union-Find / Disjoint Set Union.
    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        """Find the representative with path compression."""
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> bool:
        """
        Merge the components containing a and b.

        Returns True only when two different components are merged.
        Union by size makes the structure efficient and deterministic.
        """
        ra = find(a)
        rb = find(b)

        if ra == rb:
            return False

        # Deterministic union by size.
        # In an equal-size tie, use the smaller root as the new root.
        if size[ra] < size[rb] or (
            size[ra] == size[rb] and ra > rb
        ):
            ra, rb = rb, ra

        parent[rb] = ra
        size[ra] += size[rb]
        return True

    # Sort by weight first and original edge index second.
    sorted_edges = sorted(
        enumerate(edges),
        key=lambda item: (item[1][2], item[0]),
    )

    # Sort queries by threshold and original query index.
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0]),
    )

    answers: List[Tuple[int, int]] = [None] * len(queries)

    components = n
    largest_component = 1
    edge_pos = 0

    for query_index, threshold in sorted_queries:

        # Add every edge whose weight is <= the current threshold.
        while (
            edge_pos < len(sorted_edges)
            and sorted_edges[edge_pos][1][2] <= threshold
        ):
            _, (u, v, _) = sorted_edges[edge_pos]

            if union(u, v):
                components -= 1

                root = find(u)
                if size[root] > largest_component:
                    largest_component = size[root]

            edge_pos += 1

        answers[query_index] = (
            components,
            largest_component,
        )

    return answers


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:
    # Basic example.
    #
    # Vertices: 0, 1, 2, 3
    # Edges:
    #   0--1 with weight 2
    #   1--2 with weight 5
    #   2--3 with weight 7
    #
    # q=1: {0}, {1}, {2}, {3} -> 4 components, largest 1
    # q=5: {0,1,2}, {3}      -> 2 components, largest 3
    # q=7: {0,1,2,3}         -> 1 component, largest 4
    result = threshold_connectivity(
        4,
        [
            (0, 1, 2),
            (1, 2, 5),
            (2, 3, 7),
        ],
        [1, 5, 7],
    )

    assert result == [
        (4, 1),
        (2, 3),
        (1, 4),
    ]

    # Queries are deliberately out of order.
    result = threshold_connectivity(
        4,
        [
            (0, 1, 2),
            (1, 2, 5),
            (2, 3, 7),
        ],
        [7, 1, 5],
    )

    assert result == [
        (1, 4),
        (4, 1),
        (2, 3),
    ]

    # Equal thresholds must produce identical answers.
    result = threshold_connectivity(
        3,
        [
            (0, 1, 10),
            (1, 2, 10),
        ],
        [10, 0, 10, 10],
    )

    assert result == [
        (1, 3),
        (3, 1),
        (1, 3),
        (1, 3),
    ]

    # Disconnected graph.
    result = threshold_connectivity(
        5,
        [
            (0, 1, 3),
            (3, 4, 8),
        ],
        [0, 3, 8],
    )

    assert result == [
        (5, 1),
        (4, 2),
        (3, 2),
    ]

    # Multiple edges between the same vertices.
    result = threshold_connectivity(
        3,
        [
            (0, 1, 2),
            (0, 1, 5),
            (1, 2, 9),
        ],
        [2, 5, 9],
    )

    assert result == [
        (2, 2),
        (2, 2),
        (1, 3),
    ]

    # Self-loop does not reduce the number of components.
    result = threshold_connectivity(
        2,
        [
            (0, 0, 1),
            (0, 1, 2),
        ],
        [1, 2],
    )

    assert result == [
        (2, 1),
        (1, 2),
    ]

    # Smallest permitted non-empty graph.
    result = threshold_connectivity(
        1,
        [],
        [-100, 0, 100],
    )

    assert result == [
        (1, 1),
        (1, 1),
        (1, 1),
    ]

    # Empty graph.
    result = threshold_connectivity(
        0,
        [],
        [-1, 0, 10],
    )

    assert result == [
        (0, 0),
        (0, 0),
        (0, 0),
    ]

    # No queries.
    result = threshold_connectivity(
        3,
        [(0, 1, 1)],
        [],
    )

    assert result == []

    # Negative edge weights and thresholds.
    result = threshold_connectivity(
        3,
        [
            (0, 1, -5),
            (1, 2, 0),
        ],
        [-10, -5, 0],
    )

    assert result == [
        (3, 1),
        (2, 2),
        (1, 3),
    ]

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()