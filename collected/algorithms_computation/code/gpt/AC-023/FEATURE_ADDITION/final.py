# Threshold Connectivity Tracker
#
# Original problem:
# Given an undirected weighted graph and several threshold queries q,
# consider only edges whose weight <= q.
#
# For every query, return:
#   1. The number of connected components.
#   2. The size of the largest connected component.
#
# Existing required output:
#   [(component_count, largest_component_size), ...]
#
# New optional feature:
# When include_operation_summary=True, return:
#   {
#       "results": [(component_count, largest_component_size), ...],
#       "operation_summary": <deterministic operation count>
#   }
#
# The original output remains completely unchanged when
# include_operation_summary=False (the default).
#
# Operation summary:
# The summary reports the number of major computational DSU decisions/
# operations made by the incremental algorithm.
#
# For this implementation, one major operation is counted for every
# edge considered/activated while processing the sorted thresholds.
# Thus, each edge whose weight is <= at least one query threshold
# contributes exactly one operation.
#
# Algorithm:
# 1. Sort edges by weight.
# 2. Sort queries by threshold while preserving their original indices.
# 3. Initially every vertex is its own component.
# 4. Process queries in increasing threshold order.
# 5. Incrementally union every edge whose weight <= the current threshold.
# 6. Maintain:
#      - number of connected components
#      - largest component size
# 7. Restore the original query order.
#
# Time complexity:
#   O(E log E + Q log Q + E alpha(V))
#
# Space complexity:
#   O(V + E + Q)
#
# Standard library only. No network, APIs, external services,
# randomness, or human interaction.


from typing import List, Tuple, Union, Dict, Any


Edge = Tuple[int, int, int]
Answer = Tuple[int, int]


class DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = 1 if n > 0 else 0

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return False

        # Deterministic union-by-size.
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra

        self.parent[rb] = ra
        self.size[ra] += self.size[rb]

        self.components -= 1
        self.largest = max(self.largest, self.size[ra])

        return True


def threshold_connectivity(
    n: int,
    edges: List[Edge],
    queries: List[int],
    include_operation_summary: bool = False,
) -> Union[List[Answer], Dict[str, Any]]:
    """
    Solve Threshold Connectivity Tracker.

    Parameters:
        n:
            Number of vertices, indexed 0 through n-1.

        edges:
            Undirected weighted edges represented as (u, v, weight).

        queries:
            Threshold queries.

        include_operation_summary:
            If False, return the original list of answers.
            If True, return a dictionary containing the original
            results plus operation_summary.

    Returns:

        When include_operation_summary=False:
            [
                (component_count, largest_component_size),
                ...
            ]

        When include_operation_summary=True:
            {
                "results": [
                    (component_count, largest_component_size),
                    ...
                ],
                "operation_summary": {
                    "edge_processing_operations": <integer>
                }
            }
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge vertex is outside the valid range")

    # Sort queries by threshold and retain original positions.
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0]),
    )

    # Sort edges by weight and original edge index.
    sorted_edges = sorted(
        enumerate(edges),
        key=lambda item: (item[1][2], item[0]),
    )

    dsu = DSU(n)
    answers: List[Answer] = [None] * len(queries)  # type: ignore

    edge_index = 0
    operation_count = 0

    for query_index, threshold in sorted_queries:
        # Every edge is processed only once because thresholds
        # are handled in increasing order.
        while (
            edge_index < len(sorted_edges)
            and sorted_edges[edge_index][1][2] <= threshold
        ):
            _, (u, v, _) = sorted_edges[edge_index]

            # One major computational operation:
            # considering/activating this edge.
            operation_count += 1

            dsu.union(u, v)
            edge_index += 1

        answers[query_index] = (
            dsu.components,
            dsu.largest,
        )

    # Preserve the original behavior exactly when the optional
    # feature is not requested.
    if not include_operation_summary:
        return answers

    return {
        "results": answers,
        "operation_summary": {
            "edge_processing_operations": operation_count
        },
    }


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:
    # Original behavior remains unchanged by default.
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

    # Unsorted queries still return results in original query order.
    queries = [5, 0, 8, 2]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 3),
        (4, 1),
        (1, 4),
        (3, 2),
    ]

    # Equal thresholds.
    queries = [5, 5, 5]

    assert threshold_connectivity(n, edges, queries) == [
        (2, 3),
        (2, 3),
        (2, 3),
    ]

    # New feature: operation summary.
    queries = [0, 2, 5, 8]

    result = threshold_connectivity(
        n,
        edges,
        queries,
        include_operation_summary=True,
    )

    assert result == {
        "results": [
            (4, 1),
            (3, 2),
            (2, 3),
            (1, 4),
        ],
        "operation_summary": {
            "edge_processing_operations": 3
        },
    }

    # Only edges reached by at least one query are processed.
    n = 4
    edges = [
        (0, 1, 1),
        (1, 2, 5),
        (2, 3, 10),
    ]
    queries = [2, 3]

    result = threshold_connectivity(
        n,
        edges,
        queries,
        include_operation_summary=True,
    )

    assert result == {
        "results": [
            (3, 2),
            (3, 2),
        ],
        "operation_summary": {
            "edge_processing_operations": 1
        },
    }

    # No edges.
    result = threshold_connectivity(
        3,
        [],
        [-10, 0, 10],
        include_operation_summary=True,
    )

    assert result == {
        "results": [
            (3, 1),
            (3, 1),
            (3, 1),
        ],
        "operation_summary": {
            "edge_processing_operations": 0
        },
    }

    # Empty graph.
    result = threshold_connectivity(
        0,
        [],
        [-1, 0, 1],
        include_operation_summary=True,
    )

    assert result == {
        "results": [
            (0, 0),
            (0, 0),
            (0, 0),
        ],
        "operation_summary": {
            "edge_processing_operations": 0
        },
    }

    # Cycles and repeated edges.
    n = 4
    edges = [
        (0, 1, 1),
        (1, 2, 1),
        (0, 2, 1),
        (2, 3, 3),
        (0, 3, 4),
    ]
    queries = [1, 2, 3, 4]

    result = threshold_connectivity(
        n,
        edges,
        queries,
        include_operation_summary=True,
    )

    assert result == {
        "results": [
            (2, 3),
            (2, 3),
            (1, 4),
            (1, 4),
        ],
        "operation_summary": {
            "edge_processing_operations": 5
        },
    }

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()