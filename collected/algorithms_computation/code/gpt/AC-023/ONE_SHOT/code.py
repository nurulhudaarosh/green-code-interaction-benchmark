# Problem:
# For each weight threshold q, consider only graph edges whose weight is <= q.
# For every query threshold, return:
#   1. The number of connected components.
#   2. The size of the largest connected component.
#
# Key constraints:
# - The graph is undirected.
# - Vertices are identified by integer indices 0..n-1.
# - Each edge is (u, v, weight).
# - Each query is a weight threshold q.
# - Only edges with weight <= q are active for that query.
# - Queries must be answered deterministically.
# - The original query order must be preserved in the output.
# - No network access, APIs, external services, randomness, or human interaction.
# - Standard library only.
#
# Required output:
# Return one (component_count, largest_component_size) pair for each
# query threshold, in the same order as the input queries.
#
# Algorithm:
# 1. Sort edges by weight.
# 2. Sort queries by threshold while remembering their original indices.
# 3. Start with every vertex as a separate component.
# 4. Process queries from smallest threshold to largest.
# 5. Before answering a query q, union every edge whose weight <= q.
# 6. Maintain the number of components and the largest component size
#    incrementally.
# 7. Put each answer back at its original query position.
#
# Time complexity:
#   O(E log E + Q log Q + (E + Q) * alpha(V))
# where V is the number of vertices, E is the number of edges,
# Q is the number of queries, and alpha is the inverse Ackermann function.
#
# Space complexity:
#   O(V + E + Q)


def threshold_connectivity(n, edges, queries):
    """
    Parameters
    ----------
    n : int
        Number of vertices, labeled 0..n-1.
    edges : list[tuple[int, int, int]]
        Undirected edges represented as (u, v, weight).
    queries : list[int]
        Weight thresholds.

    Returns
    -------
    list[tuple[int, int]]
        For each query q, returns:
        (number_of_connected_components, largest_component_size)
        considering only edges with weight <= q.
    """

    if n < 0:
        raise ValueError("n must be non-negative")

    # Validate edges.
    for u, v, w in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError("edge endpoint out of range")

    # Deterministic sorting:
    # weight first, then endpoints.
    sorted_edges = sorted(edges, key=lambda e: (e[2], e[0], e[1]))

    # Store (threshold, original_index).
    sorted_queries = sorted(
        enumerate(queries),
        key=lambda item: (item[1], item[0])
    )

    # DSU / Union-Find.
    parent = list(range(n))
    size = [1] * n

    component_count = n
    largest_component = 1 if n > 0 else 0

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        nonlocal component_count, largest_component

        ra = find(a)
        rb = find(b)

        if ra == rb:
            return False

        # Union by size gives deterministic behavior because ties
        # keep the root of the first component.
        if size[ra] < size[rb]:
            ra, rb = rb, ra

        parent[rb] = ra
        size[ra] += size[rb]

        component_count -= 1
        largest_component = max(largest_component, size[ra])

        return True

    answers = [None] * len(queries)
    edge_index = 0

    for query_index, threshold in sorted_queries:
        # Activate every edge with weight <= the current threshold.
        while (
            edge_index < len(sorted_edges)
            and sorted_edges[edge_index][2] <= threshold
        ):
            u, v, _ = sorted_edges[edge_index]
            union(u, v)
            edge_index += 1

        answers[query_index] = (
            component_count,
            largest_component
        )

    return answers


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

# Basic example:
# Edges:
#   0--1 with weight 2
#   1--2 with weight 5
#   3--4 with weight 7
#
# q=1: 5 components, largest size 1
# q=2: 4 components, largest size 2
# q=5: 3 components, largest size 3
# q=7: 2 components, largest size 3
assert threshold_connectivity(
    5,
    [(0, 1, 2), (1, 2, 5), (3, 4, 7)],
    [1, 2, 5, 7]
) == [
    (5, 1),
    (4, 2),
    (3, 3),
    (2, 3),
]

# Queries can be in arbitrary order.
assert threshold_connectivity(
    5,
    [(0, 1, 2), (1, 2, 5), (3, 4, 7)],
    [7, 1, 5, 2]
) == [
    (2, 3),
    (5, 1),
    (3, 3),
    (4, 2),
]

# Repeated thresholds must produce identical deterministic answers.
assert threshold_connectivity(
    4,
    [(0, 1, 3), (1, 2, 3), (2, 3, 10)],
    [3, 3, 10, 3]
) == [
    (2, 3),
    (2, 3),
    (1, 4),
    (2, 3),
]

# No edges: every vertex remains its own component.
assert threshold_connectivity(
    4,
    [],
    [-10, 0, 100]
) == [
    (4, 1),
    (4, 1),
    (4, 1),
]

# Smallest permitted graph with one vertex.
assert threshold_connectivity(
    1,
    [],
    [-1, 0, 100]
) == [
    (1, 1),
    (1, 1),
    (1, 1),
]

# Self-loops do not change connectivity.
assert threshold_connectivity(
    3,
    [(0, 0, 1), (1, 1, 2)],
    [0, 1, 2]
) == [
    (3, 1),
    (3, 1),
    (3, 1),
]

# Multiple edges between the same vertices are handled correctly.
assert threshold_connectivity(
    3,
    [(0, 1, 1), (0, 1, 2), (1, 2, 4)],
    [1, 2, 4]
) == [
    (2, 2),
    (2, 2),
    (1, 3),
]

print("All tests passed.")