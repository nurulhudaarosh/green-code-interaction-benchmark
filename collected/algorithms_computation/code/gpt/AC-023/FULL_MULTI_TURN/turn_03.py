id="41827"
"""
Threshold Connectivity Tracker

ORIGINAL PROBLEM
----------------
Given an undirected weighted graph with n vertices and a list of threshold
queries q, answer each query independently:

    - Consider only edges whose weight <= q.
    - Return the number of connected components.
    - Return the size of the largest connected component.

Original required output for each query:
    (component_count, largest_component_size)

The answers must be returned in the same order as the original queries.

ALGORITHM
---------
1. Sort edges by weight.
2. Sort queries by threshold while keeping their original indices.
3. Start with every vertex as its own connected component.
4. Process queries from smallest threshold to largest.
5. Incrementally union every edge whose weight <= the current threshold.
6. Maintain:
       - number of connected components
       - largest component size
7. Put every answer back into its original query position.

DETERMINISTIC TIE HANDLING
---------------------------
- Equal-weight edges are processed by original edge index.
- Equal-threshold queries are processed by original query index.
- DSU union-by-size ties are resolved using the smaller representative index.
- The original output fields and their meaning are unchanged.

NEW OPTIONAL FEATURE
--------------------
An optional operation_summary field can now be requested.

When operation_summary is enabled, the function returns:

    {
        "answers": [
            (component_count, largest_component_size),
            ...
        ],
        "operation_summary": {
            "edge_sort_operations": number_of_edges,
            "query_sort_operations": number_of_queries,
            "edge_activation_operations": number_of_edges_processed,
            "successful_union_operations": number_of_component_merges,
            "union_attempt_operations": number_of_edges_processed,
            "total_major_operations": total_above_operations
        }
    }

The summary is deterministic and counts major algorithmic operations.

When operation_summary is disabled or not requested, the ORIGINAL return
format is preserved exactly:

    [
        (component_count, largest_component_size),
        ...
    ]

No original field or requirement is removed or changed.

COMPLEXITY
----------
Without the optional summary:
    O(m log m + k log k + (m + k) alpha(n))

With the summary:
    Same asymptotic complexity.

Space:
    O(n + m + k)

Only Python's standard library is used.
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
        Merge two different components.

        Deterministic tie handling:
        - Larger component becomes the parent.
        - If sizes are equal, smaller representative becomes the parent.
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
        Weighted undirected edges represented as:
            (u, v, weight)

    queries:
        Threshold values.

    operation_summary:
        Optional feature.
        - False (default): return the original list of answers.
        - True: return the original answers plus a deterministic
          operation_summary dictionary.

    Returns
    -------
    If operation_summary=False:
        [
            (component_count, largest_component_size),
            ...
        ]

    If operation_summary=True:
        {
            "answers": [...],
            "operation_summary": {...}
        }
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge contains an invalid vertex")

    dsu = DSU(n)

    component_count = n
    largest_component_size = 1 if n > 0 else 0

    # --------------------------------------------------------
    # Major operation counters
    # --------------------------------------------------------
    #
    # These are deterministic counts, not timing measurements.
    edge_sort_operations = len(edges)
    query_sort_operations = len(queries)

    edge_activation_operations = 0
    union_attempt_operations = 0
    successful_union_operations = 0

    # --------------------------------------------------------
    # Sort edges deterministically
    # --------------------------------------------------------
    #
    # Primary key: edge weight
    # Tie-breaker: original edge index
    sorted_edges = sorted(
        enumerate(edges),
        key=lambda item: (item[1][2], item[0]),
    )

    # --------------------------------------------------------
    # Sort queries by threshold
    # --------------------------------------------------------
    #
    # Primary key: threshold
    # Tie-breaker: original query index
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0]),
    )

    answers: List[Answer | None] = [None] * len(queries)

    edge_index = 0

    # --------------------------------------------------------
    # Incremental threshold processing
    # --------------------------------------------------------
    for query_index, threshold in sorted_queries:

        # Every edge with weight <= threshold becomes active.
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

        # Preserve the original query order.
        answers[query_index] = (
            component_count,
            largest_component_size,
        )

    final_answers: OriginalResult = [
        answer for answer in answers if answer is not None
    ]

    # --------------------------------------------------------
    # Preserve original behavior unless explicitly requested.
    # --------------------------------------------------------
    if not operation_summary:
        return final_answers

    total_major_operations = (
        edge_sort_operations
        + query_sort_operations
        + edge_activation_operations
        + union_attempt_operations
        + successful_union_operations
    )

    summary = {
        "edge_sort_operations": edge_sort_operations,
        "query_sort_operations": query_sort_operations,
        "edge_activation_operations": edge_activation_operations,
        "union_attempt_operations": union_attempt_operations,
        "successful_union_operations": successful_union_operations,
        "total_major_operations": total_major_operations,
    }

    return {
        "answers": final_answers,
        "operation_summary": summary,
    }


# ============================================================
# TESTS
# ============================================================

def run_tests() -> None:

    # --------------------------------------------------------
    # Test 1: Original behavior remains unchanged.
    # --------------------------------------------------------
    result = threshold_connectivity(
        3,
        [
            (0, 1, 1),
            (1, 2, 2),
        ],
        [2, 0],
    )

    assert result == [
        (1, 3),
        (3, 1),
    ]

    # --------------------------------------------------------
    # Test 2: Explicitly disabling the feature also preserves
    # the original output format.
    # --------------------------------------------------------
    result = threshold_connectivity(
        3,
        [
            (0, 1, 1),
            (1, 2, 2),
        ],
        [2, 0],
        operation_summary=False,
    )

    assert result == [
        (1, 3),
        (3, 1),
    ]

    # --------------------------------------------------------
    # Test 3: Optional operation_summary.
    # --------------------------------------------------------
    result = threshold_connectivity(
        3,
        [
            (0, 1, 1),
            (1, 2, 2),
        ],
        [2, 0],
        operation_summary=True,
    )

    assert result["answers"] == [
        (1, 3),
        (3, 1),
    ]

    summary = result["operation_summary"]

    assert summary == {
        "edge_sort_operations": 2,
        "query_sort_operations": 2,
        "edge_activation_operations": 2,
        "union_attempt_operations": 2,
        "successful_union_operations": 2,
        "total_major_operations": 10,
    }

    # --------------------------------------------------------
    # Test 4: Repeated thresholds.
    # --------------------------------------------------------
    result = threshold_connectivity(
        3,
        [
            (0, 1, 5),
            (1, 2, 5),
        ],
        [5, 5, 0, 5],
        operation_summary=True,
    )

    assert result["answers"] == [
        (1, 3),
        (1, 3),
        (3, 1),
        (1, 3),
    ]

    assert result["operation_summary"] == {
        "edge_sort_operations": 2,
        "query_sort_operations": 4,
        "edge_activation_operations": 2,
        "union_attempt_operations": 2,
        "successful_union_operations": 2,
        "total_major_operations": 12,
    }

    # --------------------------------------------------------
    # Test 5: Equal-weight edges.
    # --------------------------------------------------------
    result = threshold_connectivity(
        4,
        [
            (0, 1, 5),
            (2, 3, 5),
        ],
        [4, 5],
        operation_summary=True,
    )

    assert result["answers"] == [
        (4, 1),
        (2, 2),
    ]

    assert result["operation_summary"]["edge_activation_operations"] == 2
    assert result["operation_summary"]["successful_union_operations"] == 2

    # --------------------------------------------------------
    # Test 6: Disconnected graph.
    # --------------------------------------------------------
    result = threshold_connectivity(
        6,
        [
            (0, 1, 10),
            (1, 2, 20),
            (3, 4, 5),
        ],
        [0, 5, 10, 20],
        operation_summary=True,
    )

    assert result["answers"] == [
        (6, 1),
        (5, 2),
        (4, 2),
        (3, 3),
    ]

    assert result["operation_summary"]["successful_union_operations"] == 3

    # --------------------------------------------------------
    # Test 7: Empty graph.
    # --------------------------------------------------------
    result = threshold_connectivity(
        5,
        [],
        [-1, 0, 100],
        operation_summary=True,
    )

    assert result["answers"] == [
        (5, 1),
        (5, 1),
        (5, 1),
    ]

    assert result["operation_summary"] == {
        "edge_sort_operations": 0,
        "query_sort_operations": 3,
        "edge_activation_operations": 0,
        "union_attempt_operations": 0,
        "successful_union_operations": 0,
        "total_major_operations": 3,
    }

    # --------------------------------------------------------
    # Test 8: Smallest graph.
    # --------------------------------------------------------
    result = threshold_connectivity(
        1,
        [],
        [0],
        operation_summary=True,
    )

    assert result["answers"] == [(1, 1)]

    # --------------------------------------------------------
    # Test 9: Self-loop.
    # --------------------------------------------------------
    result = threshold_connectivity(
        1,
        [(0, 0, 7)],
        [6, 7],
        operation_summary=True,
    )

    assert result["answers"] == [
        (1, 1),
        (1, 1),
    ]

    assert result["operation_summary"]["edge_activation_operations"] == 1
    assert result["operation_summary"]["union_attempt_operations"] == 1
    assert result["operation_summary"]["successful_union_operations"] == 0

    # --------------------------------------------------------
    # Test 10: Negative values.
    # --------------------------------------------------------
    result = threshold_connectivity(
        3,
        [
            (0, 1, -10),
            (1, 2, -5),
        ],
        [-11, -10, -5],
        operation_summary=True,
    )

    assert result["answers"] == [
        (3, 1),
        (2, 2),
        (1, 3),
    ]

    # --------------------------------------------------------
    # Test 11: Cycle.
    # --------------------------------------------------------
    result = threshold_connectivity(
        4,
        [
            (0, 1, 1),
            (1, 2, 2),
            (2, 0, 3),
            (2, 3, 4),
        ],
        [2, 3, 4],
        operation_summary=True,
    )

    assert result["answers"] == [
        (2, 3),
        (2, 3),
        (1, 4),
    ]

    # Four edges are activated, but only three successfully
    # merge different components.
    assert result["operation_summary"]["edge_activation_operations"] == 4
    assert result["operation_summary"]["successful_union_operations"] == 3

    # --------------------------------------------------------
    # Test 12: Empty query list.
    # --------------------------------------------------------
    assert threshold_connectivity(
        5,
        [(0, 1, 1)],
        [],
    ) == []

    result = threshold_connectivity(
        5,
        [(0, 1, 1)],
        [],
        operation_summary=True,
    )

    assert result == {
        "answers": [],
        "operation_summary": {
            "edge_sort_operations": 1,
            "query_sort_operations": 0,
            "edge_activation_operations": 0,
            "union_attempt_operations": 0,
            "successful_union_operations": 0,
            "total_major_operations": 1,
        },
    }

    # --------------------------------------------------------
    # Test 13: Very large values.
    # --------------------------------------------------------
    LIMIT = 10**18

    result = threshold_connectivity(
        3,
        [
            (0, 1, -LIMIT),
            (1, 2, LIMIT),
        ],
        [-LIMIT, 0, LIMIT],
        operation_summary=True,
    )

    assert result["answers"] == [
        (2, 2),
        (2, 2),
        (1, 3),
    ]

    # --------------------------------------------------------
    # Test 14: All edges already active at the first query.
    # --------------------------------------------------------
    result = threshold_connectivity(
        4,
        [
            (0, 1, 1),
            (1, 2, 2),
            (2, 3, 3),
        ],
        [100, 0],
        operation_summary=True,
    )

    assert result["answers"] == [
        (1, 4),
        (4, 1),
    ]

    assert result["operation_summary"]["edge_activation_operations"] == 3
    assert result["operation_summary"]["successful_union_operations"] == 3

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()