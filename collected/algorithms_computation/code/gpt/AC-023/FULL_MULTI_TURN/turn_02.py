"""
Threshold Connectivity Tracker — Bug Report and Corrected Implementation

1. Problem Restatement
----------------------
Given an undirected weighted graph with n vertices and weighted edges, answer
each threshold query q.

For a threshold q:
    - Include every edge whose weight <= q.
    - Find the number of connected components.
    - Find the size of the largest connected component.

Expected output for each query:
    (number_of_connected_components, largest_component_size)

Answers must remain in the ORIGINAL query order.

The required algorithm is:
    - Sort edges by weight.
    - Sort queries by threshold while remembering their original indices.
    - Process queries from smallest threshold to largest.
    - Incrementally union every edge whose weight <= the current threshold.
    - Store each answer at its original query position.

Deterministic behavior:
    - Equal-weight edges are processed in a deterministic order.
    - Equal-threshold queries are processed in their original order.
    - DSU union ties are resolved deterministically.
    - No unnecessary or different output fields are introduced.


2. Bug Demonstration
--------------------
A common defect is to process queries in their input order while advancing
through edges only once.

Example:

    n = 3
    edges = [
        (0, 1, 1),
        (1, 2, 2),
    ]
    queries = [2, 0]

Correct answers:

    q = 2 -> all edges with weight <= 2:
             one component of size 3
             => (1, 3)

    q = 0 -> no edges with weight <= 0:
             three isolated components
             => (3, 1)

Therefore:

    [(1, 3), (3, 1)]

A broken input-order implementation may process q=2 first, consume both
edges, and then incorrectly answer q=0 using those already-added edges:

    [(1, 3), (1, 3)]   <-- WRONG

The defect is that the incremental DSU state only works when thresholds are
processed from smallest to largest. Sorting the queries is therefore required.


3. Corrected Implementation
---------------------------
"""

from typing import List, Tuple


class DSU:
    """Disjoint Set Union with deterministic union-by-size."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x: int) -> int:
        """Find representative with path compression."""
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

        Returns True only when two different components are merged.

        Deterministic tie handling:
        - Larger component becomes the parent.
        - If sizes are equal, smaller representative index becomes parent.
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
) -> List[Tuple[int, int]]:
    """
    Return (component_count, largest_component_size) for every threshold.

    Edges (u, v, w) are active for query q exactly when w <= q.

    The returned answers are in the same order as the original queries.
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge contains an invalid vertex")

    dsu = DSU(n)

    component_count = n
    largest_component_size = 1 if n > 0 else 0

    # Sort edges by threshold/weight.
    # Original edge index provides deterministic ordering for equal weights.
    sorted_edges = sorted(
        enumerate(edges),
        key=lambda item: (item[1][2], item[0]),
    )

    # CRITICAL FIX:
    # Sort queries by threshold, while preserving original indices.
    #
    # The original query order is used only for deterministic tie handling
    # among equal thresholds and for restoring the final output order.
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0]),
    )

    answers: List[Tuple[int, int] | None] = [None] * len(queries)

    edge_index = 0

    for query_index, threshold in sorted_queries:

        # Incrementally add all edges that are now active.
        while (
            edge_index < len(sorted_edges)
            and sorted_edges[edge_index][1][2] <= threshold
        ):
            _, (u, v, _) = sorted_edges[edge_index]

            if dsu.union(u, v):
                component_count -= 1

                root = dsu.find(u)
                largest_component_size = max(
                    largest_component_size,
                    dsu.size[root],
                )

            edge_index += 1

        # Store according to the ORIGINAL query position.
        answers[query_index] = (
            component_count,
            largest_component_size,
        )

    # Every query receives exactly one answer.
    return [answer for answer in answers if answer is not None]


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:

    # --------------------------------------------------------
    # Bug-reproducing example
    # --------------------------------------------------------
    #
    # Input-order processing would incorrectly reuse edges from
    # threshold 2 when answering threshold 0.
    #
    # Correct:
    # q=2 -> (1, 3)
    # q=0 -> (3, 1)
    #
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
    # Queries already sorted
    # --------------------------------------------------------
    assert threshold_connectivity(
        4,
        [
            (0, 1, 1),
            (1, 2, 2),
            (2, 3, 3),
        ],
        [0, 2, 3],
    ) == [
        (4, 1),
        (2, 3),
        (1, 4),
    ]


    # --------------------------------------------------------
    # Queries in reverse order
    # --------------------------------------------------------
    assert threshold_connectivity(
        4,
        [
            (0, 1, 1),
            (1, 2, 2),
            (2, 3, 3),
        ],
        [3, 2, 0],
    ) == [
        (1, 4),
        (2, 3),
        (4, 1),
    ]


    # --------------------------------------------------------
    # Repeated thresholds
    # --------------------------------------------------------
    assert threshold_connectivity(
        3,
        [
            (0, 1, 5),
            (1, 2, 5),
        ],
        [5, 5, 0, 5],
    ) == [
        (1, 3),
        (1, 3),
        (3, 1),
        (1, 3),
    ]


    # --------------------------------------------------------
    # Equal edge weights
    # --------------------------------------------------------
    #
    # Both weight-5 edges must be included when q == 5.
    assert threshold_connectivity(
        4,
        [
            (0, 1, 5),
            (2, 3, 5),
        ],
        [4, 5],
    ) == [
        (4, 1),
        (2, 2),
    ]


    # --------------------------------------------------------
    # Disconnected graph
    # --------------------------------------------------------
    assert threshold_connectivity(
        6,
        [
            (0, 1, 10),
            (1, 2, 20),
            (3, 4, 5),
        ],
        [0, 5, 10, 20],
    ) == [
        (6, 1),
        (5, 2),
        (4, 2),
        (3, 3),
    ]


    # --------------------------------------------------------
    # Empty graph
    # --------------------------------------------------------
    assert threshold_connectivity(
        5,
        [],
        [-1, 0, 100],
    ) == [
        (5, 1),
        (5, 1),
        (5, 1),
    ]


    # --------------------------------------------------------
    # Smallest graph
    # --------------------------------------------------------
    assert threshold_connectivity(
        1,
        [],
        [0],
    ) == [
        (1, 1),
    ]


    # --------------------------------------------------------
    # Self-loop
    # --------------------------------------------------------
    #
    # A self-loop does not merge two components.
    assert threshold_connectivity(
        1,
        [(0, 0, 7)],
        [6, 7],
    ) == [
        (1, 1),
        (1, 1),
    ]


    # --------------------------------------------------------
    # Negative weights and thresholds
    # --------------------------------------------------------
    assert threshold_connectivity(
        3,
        [
            (0, 1, -10),
            (1, 2, -5),
        ],
        [-11, -10, -5],
    ) == [
        (3, 1),
        (2, 2),
        (1, 3),
    ]


    # --------------------------------------------------------
    # Cycle
    # --------------------------------------------------------
    #
    # The third edge closes a cycle and therefore must not
    # decrease the component count.
    assert threshold_connectivity(
        4,
        [
            (0, 1, 1),
            (1, 2, 2),
            (2, 0, 3),
            (2, 3, 4),
        ],
        [2, 3, 4],
    ) == [
        (2, 3),
        (2, 3),
        (1, 4),
    ]


    # --------------------------------------------------------
    # Very large values
    # --------------------------------------------------------
    LIMIT = 10**18

    assert threshold_connectivity(
        3,
        [
            (0, 1, -LIMIT),
            (1, 2, LIMIT),
        ],
        [-LIMIT, 0, LIMIT],
    ) == [
        (2, 2),
        (2, 2),
        (1, 3),
    ]


    # --------------------------------------------------------
    # Empty query list
    # --------------------------------------------------------
    assert threshold_connectivity(
        5,
        [(0, 1, 1)],
        [],
    ) == []


    print("All tests passed.")


if __name__ == "__main__":
    run_tests()