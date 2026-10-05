"""
Threshold Connectivity Tracker

PROBLEM RESTATEMENT
-------------------
Given an undirected weighted graph with n vertices and a set of threshold
queries q, answer every query as follows:

For a threshold q:
    1. Consider only edges whose weight <= q.
    2. Determine the number of connected components.
    3. Determine the size of the largest connected component.

Required original output:
    [
        (number_of_connected_components, largest_component_size),
        ...
    ]

The answers must be returned in the SAME ORDER as the original queries.

Required algorithm:
    - Sort edges by weight.
    - Sort queries by threshold while remembering their original indices.
    - Process queries from smallest threshold to largest.
    - Incrementally union every edge with weight <= the current threshold.
    - Restore answers to the original query order.

Original deterministic tie-breaking rules:
    - Equal-weight edges are processed by their original edge index.
    - Equal-threshold queries are processed by their original query index.
    - DSU union-by-size ties are resolved using the smaller representative
      index.
    - Edges with weight exactly equal to q ARE included.

OPTIONAL FEATURE PRESERVED
--------------------------
If operation_summary=False (default), the original output is returned.

If operation_summary=True, the result is:

    {
        "answers": [
            (component_count, largest_component_size),
            ...
        ],
        "operation_summary": {
            ...
        }
    }

This version explicitly handles boundary values at the input limits.

BOUNDARY-VALUE HANDLING
-----------------------
Python integers do not overflow, so very large valid integer values can be
compared directly.

The implementation also handles:
    - n = 0
    - n = 1
    - no edges
    - no queries
    - minimum/maximum edge weights
    - minimum/maximum query thresholds
    - negative boundary values
    - repeated boundary thresholds
    - edges whose weight is exactly the boundary/query value

No randomness, network access, APIs, external services, or non-standard
libraries are used.
"""

from typing import Dict, List, Tuple, Union


Answer = Tuple[int, int]
OriginalResult = List[Answer]
SummaryResult = Dict[str, Union[OriginalResult, Dict[str, int]]]


class DSU:
    """Disjoint Set Union with deterministic tie handling."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        """Find representative using path compression."""
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
        Merge two components.

        Deterministic tie handling:
        - Larger component becomes the parent.
        - Equal sizes use the smaller representative index.
        """
        root_a = self.find(a)
        root_b = self.find(b)

        if root_a == root_b:
            return False

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


def threshold_connectivity(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
    operation_summary: bool = False,
) -> Union[OriginalResult, SummaryResult]:
    """
    Answer threshold connectivity queries.

    Parameters
    ----------
    n:
        Number of vertices, numbered 0 through n - 1.

    edges:
        Weighted undirected edges:
            (u, v, weight)

    queries:
        Threshold values.

    operation_summary:
        False -> original output only.
        True  -> original answers plus deterministic operation summary.

    Returns
    -------
    OriginalResult or SummaryResult
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge contains an invalid vertex")

    # Initially every vertex is its own component.
    dsu = DSU(n)

    component_count = n
    largest_component_size = 1 if n > 0 else 0

    # Deterministic edge ordering:
    #   first by weight, then by original edge index.
    sorted_edges = sorted(
        enumerate(edges),
        key=lambda item: (item[1][2], item[0]),
    )

    # Deterministic query ordering:
    #   first by threshold, then by original query index.
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0]),
    )

    answers: List[Answer | None] = [None] * len(queries)

    # Optional operation counters.
    edge_sort_operations = len(edges)
    query_sort_operations = len(queries)
    edge_activation_operations = 0
    union_attempt_operations = 0
    successful_union_operations = 0

    edge_index = 0

    # Process thresholds in ascending order.
    for query_index, threshold in sorted_queries:

        # Activate every edge whose weight <= threshold.
        while (
            edge_index < len(sorted_edges)
            and sorted_edges[edge_index][1][2] <= threshold
        ):
            _, (u, v, _) = sorted_edges[edge_index]

            edge_activation_operations += 1
            union_attempt_operations += 1

            if dsu.union(u, v):
                successful_union_operations += 1
                component_count -= 1

                root = dsu.find(u)
                if dsu.size[root] > largest_component_size:
                    largest_component_size = dsu.size[root]

            edge_index += 1

        # Restore original query order.
        answers[query_index] = (
            component_count,
            largest_component_size,
        )

    final_answers: OriginalResult = [
        answer for answer in answers if answer is not None
    ]

    # Preserve the original result exactly when the feature is disabled.
    if not operation_summary:
        return final_answers

    total_major_operations = (
        edge_sort_operations
        + query_sort_operations
        + edge_activation_operations
        + union_attempt_operations
        + successful_union_operations
    )

    return {
        "answers": final_answers,
        "operation_summary": {
            "edge_sort_operations": edge_sort_operations,
            "query_sort_operations": query_sort_operations,
            "edge_activation_operations": edge_activation_operations,
            "union_attempt_operations": union_attempt_operations,
            "successful_union_operations": successful_union_operations,
            "total_major_operations": total_major_operations,
        },
    }


# ============================================================
# TESTS
# ============================================================

def run_tests() -> None:

    # --------------------------------------------------------
    # 1. Original basic behavior
    # --------------------------------------------------------
    assert threshold_connectivity(
        3,
        [
            (0, 1, 1),
            (1, 2, 2),
        ],
        [2, 0],
    ) == [
        (1, 3),
        (3, 1),
    ]


    # --------------------------------------------------------
    # 2. Boundary: n = 0
    # --------------------------------------------------------
    #
    # Empty graph, no vertices, arbitrary thresholds.
    assert threshold_connectivity(
        0,
        [],
        [-10**18, 0, 10**18],
    ) == [
        (0, 0),
        (0, 0),
        (0, 0),
    ]


    # --------------------------------------------------------
    # 3. Boundary: n = 1
    # --------------------------------------------------------
    #
    # One isolated vertex always forms one component of size 1.
    assert threshold_connectivity(
        1,
        [],
        [-10**18, 0, 10**18],
    ) == [
        (1, 1),
        (1, 1),
        (1, 1),
    ]


    # --------------------------------------------------------
    # 4. Minimum and maximum signed 64-bit-style values
    # --------------------------------------------------------
    #
    # These values are commonly used as practical integer input limits.
    MIN_LIMIT = -(2**63)
    MAX_LIMIT = 2**63 - 1

    assert threshold_connectivity(
        3,
        [
            (0, 1, MIN_LIMIT),
            (1, 2, MAX_LIMIT),
        ],
        [
            MIN_LIMIT - 1,
            MIN_LIMIT,
            0,
            MAX_LIMIT,
        ],
    ) == [
        (3, 1),
        (2, 2),
        (2, 2),
        (1, 3),
    ]


    # --------------------------------------------------------
    # 5. Exact boundary equality
    # --------------------------------------------------------
    #
    # An edge with weight exactly q must be included.
    assert threshold_connectivity(
        2,
        [
            (0, 1, MAX_LIMIT),
        ],
        [
            MAX_LIMIT - 1,
            MAX_LIMIT,
        ],
    ) == [
        (2, 1),
        (1, 2),
    ]


    # --------------------------------------------------------
    # 6. Negative boundary equality
    # --------------------------------------------------------
    assert threshold_connectivity(
        2,
        [
            (0, 1, MIN_LIMIT),
        ],
        [
            MIN_LIMIT - 1,
            MIN_LIMIT,
        ],
    ) == [
        (2, 1),
        (1, 2),
    ]


    # --------------------------------------------------------
    # 7. Boundary values with repeated queries
    # --------------------------------------------------------
    assert threshold_connectivity(
        3,
        [
            (0, 1, MIN_LIMIT),
            (1, 2, MAX_LIMIT),
        ],
        [
            MAX_LIMIT,
            MIN_LIMIT,
            MAX_LIMIT,
            MIN_LIMIT,
        ],
    ) == [
        (1, 3),
        (2, 2),
        (1, 3),
        (2, 2),
    ]


    # --------------------------------------------------------
    # 8. Boundary values with unsorted queries
    # --------------------------------------------------------
    assert threshold_connectivity(
        4,
        [
            (0, 1, MAX_LIMIT),
            (2, 3, MIN_LIMIT),
        ],
        [
            MAX_LIMIT,
            MIN_LIMIT - 1,
            MIN_LIMIT,
            MAX_LIMIT - 1,
        ],
    ) == [
        (1, 4),
        (4, 1),
        (3, 2),
        (3, 2),
    ]


    # --------------------------------------------------------
    # 9. Equal boundary edge weights
    # --------------------------------------------------------
    #
    # Both edges must be activated at exactly MIN_LIMIT.
    assert threshold_connectivity(
        4,
        [
            (0, 1, MIN_LIMIT),
            (2, 3, MIN_LIMIT),
        ],
        [
            MIN_LIMIT - 1,
            MIN_LIMIT,
        ],
    ) == [
        (4, 1),
        (2, 2),
    ]


    # --------------------------------------------------------
    # 10. Boundary self-loop
    # --------------------------------------------------------
    #
    # The self-loop is processed but does not merge components.
    assert threshold_connectivity(
        1,
        [
            (0, 0, MAX_LIMIT),
        ],
        [
            MAX_LIMIT - 1,
            MAX_LIMIT,
        ],
    ) == [
        (1, 1),
        (1, 1),
    ]


    # --------------------------------------------------------
    # 11. Boundary cycle
    # --------------------------------------------------------
    #
    # The third edge closes a cycle and must not reduce the
    # component count again.
    assert threshold_connectivity(
        3,
        [
            (0, 1, MIN_LIMIT),
            (1, 2, MIN_LIMIT),
            (2, 0, MAX_LIMIT),
        ],
        [
            MIN_LIMIT,
            MAX_LIMIT,
        ],
    ) == [
        (1, 3),
        (1, 3),
    ]


    # --------------------------------------------------------
    # 12. Empty edges at boundary thresholds
    # --------------------------------------------------------
    assert threshold_connectivity(
        5,
        [],
        [
            MIN_LIMIT,
            MAX_LIMIT,
        ],
    ) == [
        (5, 1),
        (5, 1),
    ]


    # --------------------------------------------------------
    # 13. Empty queries
    # --------------------------------------------------------
    assert threshold_connectivity(
        5,
        [
            (0, 1, MIN_LIMIT),
        ],
        [],
    ) == []


    # --------------------------------------------------------
    # 14. Operation summary remains optional
    # --------------------------------------------------------
    #
    # Disabled -> original format only.
    original = threshold_connectivity(
        2,
        [(0, 1, MAX_LIMIT)],
        [MAX_LIMIT],
    )

    assert original == [(1, 2)]


    # Enabled -> original answers plus summary.
    with_summary = threshold_connectivity(
        2,
        [(0, 1, MAX_LIMIT)],
        [MAX_LIMIT],
        operation_summary=True,
    )

    assert with_summary["answers"] == [(1, 2)]

    assert with_summary["operation_summary"] == {
        "edge_sort_operations": 1,
        "query_sort_operations": 1,
        "edge_activation_operations": 1,
        "union_attempt_operations": 1,
        "successful_union_operations": 1,
        "total_major_operations": 5,
    }


    # --------------------------------------------------------
    # 15. Very large Python integers beyond 64-bit boundaries
    # --------------------------------------------------------
    #
    # Python supports arbitrary-precision integers, so the algorithm
    # remains correct even beyond typical machine integer limits.
    HUGE = 10**100

    assert threshold_connectivity(
        2,
        [(0, 1, HUGE)],
        [HUGE - 1, HUGE],
    ) == [
        (2, 1),
        (1, 2),
    ]


    print("All tests passed.")


if __name__ == "__main__":
    run_tests()