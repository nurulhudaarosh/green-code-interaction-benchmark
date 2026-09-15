import heapq


def single_source_route_analyzer(n, edges, source, include_operation_summary=False):
    """
    Compute shortest distances from `source` to every vertex.

    When include_operation_summary is False:
        Returns the original list of distances.

    When include_operation_summary is True:
        Returns:
        {
            "distances": [...],
            "operation_summary": {
                "major_operations": <count>
            }
        }
    """

    # Adjacency-list representation.
    graph = [[] for _ in range(n)]

    for u, v, weight in edges:
        graph[u].append((v, weight))

    # Deterministic adjacency traversal.
    for neighbors in graph:
        neighbors.sort(key=lambda item: (item[0], item[1]))

    INF = float("inf")
    dist = [INF] * n
    dist[source] = 0

    # Binary heap.
    # Vertex ID provides deterministic tie handling.
    heap = [(0, source)]

    major_operations = 0

    while heap:
        current_dist, u = heapq.heappop(heap)

        # Ignore stale entries.
        if current_dist != dist[u]:
            continue

        for v, weight in graph[u]:
            # One major computational decision:
            # determine whether this edge improves dist[v].
            major_operations += 1

            new_dist = current_dist + weight

            if new_dist < dist[v]:
                dist[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    distances = [-1 if d == INF else d for d in dist]

    # Preserve the original output when the feature is not requested.
    if not include_operation_summary:
        return distances

    return {
        "distances": distances,
        "operation_summary": {
            "major_operations": major_operations
        }
    }


# Example
if __name__ == "__main__":
    n = 4
    edges = [
        (0, 1, 1),
        (0, 2, 1),
        (1, 3, 1),
        (2, 3, 1),
    ]

    # Original behavior
    print(single_source_route_analyzer(n, edges, 0))

    # New optional behavior
    print(single_source_route_analyzer(
        n, edges, 0, include_operation_summary=True
    ))