import heapq
from typing import Dict, List, Tuple, Hashable

def dijkstra(
    adjacency: Dict[Hashable, List[Tuple[Hashable, float]]],
    source: Hashable
) -> Dict[Hashable, float]:
    """
    Compute shortest distances from `source` to all vertices in a directed
    graph with non-negative edge weights.

    adjacency: maps vertex -> list of (neighbor, weight) tuples.
               All vertices (including those with no outgoing edges) must
               appear as keys.
    source: the starting vertex. Must be a key in adjacency.

    Returns: dict mapping every vertex to its shortest distance from source,
             or -1 if unreachable.
    """
    if source not in adjacency:
        raise ValueError(f"Source vertex {source!r} not in graph")

    dist = {v: float('inf') for v in adjacency}
    dist[source] = 0

    # (distance, vertex) — heapq compares tuples, distance first, deterministic
    # tie-breaking requires vertices be comparable OR we avoid comparing them
    # by using a counter as a tiebreaker.
    counter = 0
    heap: List[Tuple[float, int, Hashable]] = [(0, counter, source)]
    visited = set()

    while heap:
        d, _, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)

        for v, w in adjacency.get(u, []):
            if w < 0:
                raise ValueError("Edge weights must be non-negative")
            if v not in dist:
                dist[v] = float('inf')
            new_dist = d + w
            if new_dist < dist[v]:
                dist[v] = new_dist
                counter += 1
                heapq.heappush(heap, (new_dist, counter, v))

    # Convert unreachable (inf) distances to -1
    return {v: (-1 if d == float('inf') else d) for v, d in dist.items()}


if __name__ == "__main__":
    # Deterministic example graph
    graph = {
        'A': [('B', 4), ('C', 1)],
        'B': [('D', 1)],
        'C': [('B', 2), ('D', 5)],
        'D': [],
        'E': [],  # unreachable from A
    }

    result = dijkstra(graph, 'A')
    for vertex in sorted(result.keys()):
        print(f"{vertex}: {result[vertex]}")