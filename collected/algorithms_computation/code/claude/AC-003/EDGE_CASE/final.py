import heapq
import unittest
from typing import Dict, List, Tuple, Hashable


def dijkstra(
    adjacency: Dict[Hashable, List[Tuple[Hashable, float]]],
    source: Hashable
) -> Dict[Hashable, float]:
    """
    Compute shortest distances from `source` to all vertices in a directed
    graph with non-negative edge weights.

    adjacency: maps vertex -> list of (neighbor, weight) tuples.
               Neighbors that appear only as edge targets (not as their own
               key) are automatically included as vertices with no outgoing
               edges.
    source: the starting vertex. Must be a key in adjacency.

    Returns: dict mapping every vertex to its shortest distance from source,
             or -1 if unreachable. Deterministic tie-breaking via an
             insertion-order counter in the heap.
    """
    if source not in adjacency:
        raise ValueError(f"Source vertex {source!r} not in graph")

    # Boundary case 9: ensure every edge target is a known vertex, even if
    # it has no outgoing edges of its own.
    vertices = set(adjacency.keys())
    for u, edges in adjacency.items():
        for v, _ in edges:
            vertices.add(v)

    dist = {v: float('inf') for v in vertices}
    dist[source] = 0

    counter = 0  # deterministic tiebreaker, preserved from original design
    heap: List[Tuple[float, int, Hashable]] = [(0, counter, source)]
    visited = set()

    while heap:
        d, _, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)

        for v, w in adjacency.get(u, []):
            if w < 0:
                raise ValueError(
                    f"Edge weights must be non-negative (got {w} on edge {u}->{v})"
                )
            new_dist = d + w
            if new_dist < dist[v]:
                dist[v] = new_dist
                counter += 1
                heapq.heappush(heap, (new_dist, counter, v))

    return {v: (-1 if d == float('inf') else d) for v, d in dist.items()}


class TestDijkstraBoundaries(unittest.TestCase):

    def test_empty_graph_raises(self):
        with self.assertRaises(ValueError):
            dijkstra({}, 'A')

    def test_single_vertex_no_edges(self):
        graph = {'A': []}
        self.assertEqual(dijkstra(graph, 'A'), {'A': 0})

    def test_source_no_outgoing_edges_other_vertices_exist(self):
        graph = {'A': [], 'B': [('C', 5)], 'C': []}
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': -1, 'C': -1})

    def test_self_loop_on_source_ignored(self):
        graph = {'A': [('A', 7), ('B', 2)], 'B': []}
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': 2})

    def test_zero_weight_edges(self):
        graph = {'A': [('B', 0)], 'B': [('C', 0)], 'C': []}
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': 0, 'C': 0})

    def test_negative_weight_raises(self):
        graph = {'A': [('B', -1)], 'B': []}
        with self.assertRaises(ValueError):
            dijkstra(graph, 'A')

    def test_parallel_edges_shortest_wins(self):
        graph = {'A': [('B', 10), ('B', 3), ('B', 7)], 'B': []}
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': 3})

    def test_disconnected_component(self):
        graph = {'A': [('B', 1)], 'B': [], 'C': [('D', 1)], 'D': []}
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': 1, 'C': -1, 'D': -1})

    def test_edge_target_not_a_key(self):
        # 'B' is never a key in adjacency, only appears as an edge target
        graph = {'A': [('B', 4)]}
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': 4})

    def test_large_weight_values(self):
        big = 10**15
        graph = {'A': [('B', big)], 'B': [('C', big)], 'C': []}
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': big, 'C': 2 * big})

    def test_tie_breaking_deterministic(self):
        # Two equal-length paths A->C: via B (1+1=2) and direct (2).
        # Result distance must be correct regardless of tie; determinism is
        # about reproducible internal ordering, verified by repeated runs.
        graph = {'A': [('B', 1), ('C', 2)], 'B': [('C', 1)], 'C': []}
        result1 = dijkstra(graph, 'A')
        result2 = dijkstra(graph, 'A')
        self.assertEqual(result1, {'A': 0, 'B': 1, 'C': 2})
        self.assertEqual(result1, result2)  # same output every run

    def test_original_example_preserved(self):
        graph = {
            'A': [('B', 4), ('C', 1)],
            'B': [('D', 1)],
            'C': [('B', 2), ('D', 5)],
            'D': [],
            'E': [],
        }
        result = dijkstra(graph, 'A')
        self.assertEqual(result, {'A': 0, 'B': 3, 'C': 1, 'D': 4, 'E': -1})


if __name__ == "__main__":
    unittest.main(verbosity=2)