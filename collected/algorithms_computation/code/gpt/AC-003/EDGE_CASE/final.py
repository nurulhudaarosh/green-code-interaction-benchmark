from heapq import heappush, heappop
from typing import List, Tuple


def single_source_route_analyzer(
    n: int,
    edges: List[Tuple[int, int, int]],
    source: int
) -> List[int]:
    """
    Return the shortest distance from source to every vertex.

    Vertices are numbered 0 through n - 1.
    Unreachable vertices are represented by -1.

    Dijkstra's algorithm with an adjacency list and binary heap
    is used. Edge weights must be non-negative.
    """

    if n <= 0:
        raise ValueError("n must be positive")

    if not 0 <= source < n:
        raise ValueError("source must be a valid vertex")

    # Adjacency list.
    adj = [[] for _ in range(n)]

    for u, v, weight in edges:
        if not 0 <= u < n or not 0 <= v < n:
            raise ValueError("edge contains an invalid vertex")

        if weight < 0:
            raise ValueError("edge weights must be non-negative")

        adj[u].append((v, weight))

    # Shortest known distances.
    INF = float("inf")
    dist = [INF] * n
    dist[source] = 0

    # Binary min-heap.
    # Python's tuple ordering also gives deterministic tie handling:
    # equal distances are ordered by vertex number.
    heap = [(0, source)]

    while heap:
        current_dist, u = heappop(heap)

        # Ignore stale entries.
        if current_dist != dist[u]:
            continue

        for v, weight in adj[u]:
            new_dist = current_dist + weight

            if new_dist < dist[v]:
                dist[v] = new_dist
                heappush(heap, (new_dist, v))

    return [-1 if d == INF else int(d) for d in dist]


# ============================================================
# Tests
# ============================================================

def run_tests():
    # 1. Smallest valid graph.
    assert single_source_route_analyzer(
        1,
        [],
        0
    ) == [0]

    # 2. Smallest graph with a self-loop.
    # The zero-cost path to the source remains optimal.
    assert single_source_route_analyzer(
        1,
        [(0, 0, 0)],
        0
    ) == [0]

    # 3. Source is the last vertex.
    assert single_source_route_analyzer(
        4,
        [(3, 2, 5), (2, 1, 2), (1, 0, 1)],
        3
    ) == [8, 7, 5, 0]

    # 4. All other vertices unreachable.
    assert single_source_route_analyzer(
        5,
        [],
        0
    ) == [0, -1, -1, -1, -1]

    # 5. Zero-weight edges.
    assert single_source_route_analyzer(
        4,
        [(0, 1, 0), (1, 2, 0), (2, 3, 0)],
        0
    ) == [0, 0, 0, 0]

    # 6. Equal shortest paths.
    # Both 0 -> 1 -> 3 and 0 -> 2 -> 3 cost 5.
    # Distance output must remain deterministic and unchanged.
    assert single_source_route_analyzer(
        4,
        [
            (0, 1, 2),
            (0, 2, 3),
            (1, 3, 3),
            (2, 3, 2),
        ],
        0
    ) == [0, 2, 3, 5]

    # 7. Duplicate edges.
    # The smaller parallel edge must determine the shortest distance.
    assert single_source_route_analyzer(
        3,
        [
            (0, 1, 10),
            (0, 1, 3),
            (1, 2, 4),
        ],
        0
    ) == [0, 3, 7]

    # 8. Large edge weight.
    # Python integers avoid fixed-width overflow.
    MAX_WEIGHT = 10**18

    assert single_source_route_analyzer(
        3,
        [
            (0, 1, MAX_WEIGHT),
            (1, 2, MAX_WEIGHT),
        ],
        0
    ) == [0, MAX_WEIGHT, 2 * MAX_WEIGHT]

    # 9. Maximum-style dense edge count test.
    # This constructs a graph with n vertices and n*(n-1) directed
    # edges, exercising a high edge-count boundary pattern.
    n = 50
    dense_edges = [
        (u, v, 1)
        for u in range(n)
        for v in range(n)
        if u != v
    ]

    result = single_source_route_analyzer(n, dense_edges, 0)

    assert result[0] == 0
    assert all(distance == 1 for distance in result[1:])

    # 10. Long chain.
    # Exercises a large number of successive relaxations.
    n = 1000
    chain_edges = [
        (i, i + 1, 1)
        for i in range(n - 1)
    ]

    result = single_source_route_analyzer(n, chain_edges, 0)

    assert result == list(range(n))

    # 11. Invalid negative weight must be rejected.
    try:
        single_source_route_analyzer(
            2,
            [(0, 1, -1)],
            0
        )
        assert False, "Negative weight should raise ValueError"
    except ValueError:
        pass

    # 12. Invalid source must be rejected.
    try:
        single_source_route_analyzer(
            2,
            [(0, 1, 1)],
            2
        )
        assert False, "Invalid source should raise ValueError"
    except ValueError:
        pass

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()