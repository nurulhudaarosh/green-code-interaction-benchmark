# Problem:
# For each weight threshold q, consider only graph edges whose weight <= q.
# For that subgraph, return:
#   1. The number of connected components.
#   2. The size of the largest connected component.
#
# Key constraints / requirements:
# - The graph has n vertices, identified by 0..n-1.
# - Each edge is (u, v, weight).
# - Edges with weight <= q are active for query q.
# - Queries must be answered deterministically.
# - Vertices with no active edges are still individual connected components.
# - Multiple edges and repeated weights are allowed.
# - Queries with the same threshold must produce the same result.
# - Only Python's standard library is used.
# - No network access, APIs, external services, randomness, or human interaction.
#
# Required output:
# Return one (component_count, largest_component_size) pair for each
# query, in the same order as the input queries.
#
# Algorithm:
# 1. Sort edges by weight.
# 2. Sort queries by threshold while remembering their original indices.
# 3. Start with n separate components.
# 4. For each query threshold q, union every not-yet-processed edge
#    whose weight <= q.
# 5. Maintain the number of components and the largest component size
#    incrementally using a Disjoint Set Union (DSU / Union-Find).
# 6. Store each answer at its original query position.
#
# Time complexity:
# - Sorting edges: O(m log m)
# - Sorting queries: O(k log k)
# - DSU operations: O((n + m) * alpha(n))
# - Total: O(m log m + k log k + (n + m) * alpha(n))
#
# Space complexity:
# - O(n + m + k)


from typing import List, Tuple


def threshold_components(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
) -> List[Tuple[int, int]]:
    """
    Return (number_of_components, largest_component_size)
    for every threshold in queries.

    Vertices are numbered 0..n-1.
    An edge (u, v, w) is active for threshold q iff w <= q.
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    for u, v, w in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge vertex out of range")

    # DSU state.
    parent = list(range(n))
    size = [1] * n

    # Initially every vertex is its own component.
    component_count = n
    largest_component = 1 if n > 0 else 0

    def find(x: int) -> int:
        """Find the representative using path compression."""
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> bool:
        """
        Merge the components containing a and b.
        Return True if a merge actually occurred.
        """
        nonlocal component_count, largest_component

        ra = find(a)
        rb = find(b)

        if ra == rb:
            return False

        # Union by size gives deterministic and efficient DSU behavior.
        if size[ra] < size[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        size[ra] += size[rb]

        component_count -= 1
        largest_component = max(largest_component, size[ra])

        return True

    # Sort edges by (weight, u, v) for deterministic processing.
    sorted_edges = sorted(edges, key=lambda e: (e[2], e[0], e[1]))

    # Keep original query indices so answers are returned in input order.
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
            and sorted_edges[edge_index][2] <= threshold
        ):
            u, v, _ = sorted_edges[edge_index]
            union(u, v)
            edge_index += 1

        answers[query_index] = (
            component_count,
            largest_component,
        )

    return answers


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:
    # Basic example.
    n = 5
    edges = [
        (0, 1, 2),
        (1, 2, 4),
        (3, 4, 6),
        (2, 3, 8),
    ]
    queries = [0, 2, 5, 6, 8]

    assert threshold_components(n, edges, queries) == [
        (5, 1),  # No edges.
        (4, 2),  # 0-1.
        (3, 3),  # 0-1-2.
        (2, 3),  # 3-4.
        (1, 5),  # Entire graph connected.
    ]

    # Queries may be out of order; answers remain in input order.
    queries = [6, 0, 8, 2]
    assert threshold_components(n, edges, queries) == [
        (2, 3),
        (5, 1),
        (1, 5),
        (4, 2),
    ]

    # Repeated thresholds.
    queries = [4, 4, 4]
    assert threshold_components(3, [(0, 1, 4)], queries) == [
        (2, 2),
        (2, 2),
        (2, 2),
    ]

    # Repeated edges and self-loop.
    edges = [
        (0, 1, 1),
        (0, 1, 1),
        (1, 1, 1),
    ]
    assert threshold_components(3, edges, [0, 1]) == [
        (3, 1),
        (2, 2),
    ]

    # Negative edge weights and thresholds are valid.
    edges = [
        (0, 1, -5),
        (1, 2, 0),
    ]
    assert threshold_components(3, edges, [-10, -5, 0]) == [
        (3, 1),
        (2, 2),
        (1, 3),
    ]

    # Empty graph.
    assert threshold_components(4, [], [-100, 0, 100]) == [
        (4, 1),
        (4, 1),
        (4, 1),
    ]

    # Single vertex.
    assert threshold_components(1, [], [0]) == [(1, 1)]

    # Empty graph with zero vertices.
    assert threshold_components(0, [], [0, 10]) == [
        (0, 0),
        (0, 0),
    ]

    # No queries.
    assert threshold_components(5, [(0, 1, 1)], []) == []

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()