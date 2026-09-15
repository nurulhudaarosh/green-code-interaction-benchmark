"""
MINIMUM SPANNING FOREST (Kruskal's Algorithm + Disjoint Set Union)
====================================================================

PROBLEM
-------
Given an undirected, weighted graph (possibly disconnected, possibly with
multiple components), construct a Minimum Spanning Forest (MSF): a
minimum-total-weight set of edges that connects every vertex to all other
vertices reachable from it, containing no cycles. If the graph is already
connected, the MSF is a Minimum Spanning Tree (MST).

Return:
  1. The total cost (sum of weights) of the selected edges.
  2. The list of original edge IDs that were selected.

KEY CONSTRAINTS
----------------
- The graph is undirected and weighted (weights may be any real/int number,
  including 0 or negative — Kruskal's algorithm works regardless of sign).
- The graph may be disconnected -> result is a *forest*, not necessarily
  a single tree.
- Each edge has a unique original ID that must be preserved and reported.
- Determinism is required: when multiple edges tie on weight, they must be
  considered in ascending order of their original edge ID. This guarantees
  a single, reproducible answer instead of one that depends on input order,
  hash iteration order, or an unstable sort.
- No external randomness, network access, or non-standard-library
  dependencies may be used.
- Must scale reasonably: O(E log E) for sorting + near O(E * alpha(V)) for
  DSU operations (alpha = inverse Ackermann, effectively constant).

REQUIRED OUTPUT
---------------
- total_cost: numeric sum of weights of edges chosen for the forest.
- selected_edge_ids: list of original edge IDs included in the forest,
  in the order they were added (i.e., ascending (weight, id) order).

ALGORITHM (Kruskal's + DSU)
----------------------------
1. Sort all edges by (weight, original_id) ascending — this ordering
   itself is what makes tie-breaking deterministic.
2. Initialize a Disjoint Set Union (Union-Find) structure with each
   vertex in its own singleton set.
3. Iterate edges in sorted order. For each edge (u, v, w, id):
     - If find(u) != find(v): the edge connects two different components,
       so it cannot create a cycle. Add it to the forest, union the sets,
       add w to total_cost, record its id.
     - Else: discard it (it would form a cycle).
4. Stop early once (V - number_of_components) edges have been chosen
   (optional optimization); otherwise just exhaust the sorted list.
5. Return total_cost and selected_edge_ids.

DSU uses union by size/rank plus path compression, giving amortized
near-constant time per operation.
"""

from typing import List, Tuple, Dict, Any


class DSU:
    """Disjoint Set Union (Union-Find) with path compression and union by rank."""

    def __init__(self, vertices):
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, x):
        # Path compression (iterative to avoid recursion limits on large inputs)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False  # already connected -> would form a cycle
        # Union by rank
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def minimum_spanning_forest(
    vertices: List[Any],
    edges: List[Tuple[int, Any, Any, float]],
) -> Dict[str, Any]:
    """
    Compute the Minimum Spanning Forest using Kruskal's algorithm.

    Args:
        vertices: list of all vertex labels in the graph.
        edges: list of (edge_id, u, v, weight) tuples. edge_id must be a
               unique, comparable identifier (e.g., an int).

    Returns:
        {
          "total_cost": <sum of weights of selected edges>,
          "selected_edge_ids": [<edge ids in the order added>]
        }
    """
    # Step 1: deterministic ordering — sort by (weight, edge_id).
    sorted_edges = sorted(edges, key=lambda e: (e[3], e[0]))

    dsu = DSU(vertices)

    total_cost = 0
    selected_edge_ids: List[Any] = []

    remaining_to_connect = len(vertices) - 1  # edges needed for full spanning tree
    if remaining_to_connect < 0:
        remaining_to_connect = 0

    for edge_id, u, v, w in sorted_edges:
        if remaining_to_connect == 0:
            break  # forest is already maximal (all components internally spanned)
        if dsu.union(u, v):
            total_cost += w
            selected_edge_ids.append(edge_id)
            remaining_to_connect -= 1

    return {
        "total_cost": total_cost,
        "selected_edge_ids": selected_edge_ids,
    }


def _parse_stdin_graph():
    """
    Reads a graph from stdin in the format:

        n m
        u1 v1 w1
        u2 v2 w2
        ...
        um vm wm

    - n: number of vertices, labeled 0..n-1
    - m: number of edges
    - each edge line: endpoints (u, v) and weight (w)
    - the original edge ID is its 0-based position in the input (line order),
      which is a natural, unambiguous, deterministic ID assignment.

    Returns (vertices, edges) suitable for minimum_spanning_forest().
    """
    import sys

    data = sys.stdin.read().split()
    idx = 0
    n = int(data[idx]); idx += 1
    m = int(data[idx]); idx += 1

    vertices = list(range(n))
    edges = []
    for edge_id in range(m):
        u = int(data[idx]); idx += 1
        v = int(data[idx]); idx += 1
        w = float(data[idx]); idx += 1
        # Store weight as int if it has no fractional part, for clean output.
        if w.is_integer():
            w = int(w)
        edges.append((edge_id, u, v, w))

    return vertices, edges


def main():
    import sys

    if not sys.stdin.isatty():
        try:
            vertices, edges = _parse_stdin_graph()
        except (IndexError, ValueError):
            vertices, edges = None, None
    else:
        vertices, edges = None, None

    if vertices is None:
        # Fallback demonstration graph (used when no valid stdin input is given).
        # Vertices: 0..5, includes a disconnected component (4-5) to show
        # forest behavior, and a tie on weight to show deterministic ID order.
        vertices = [0, 1, 2, 3, 4, 5]
        edges = [
            (0, 0, 1, 4),
            (1, 0, 2, 4),   # ties with edge 0 on weight -> lower id (0) wins first
            (2, 1, 2, 2),
            (3, 2, 3, 3),
            (4, 1, 3, 5),
            (5, 4, 5, 1),   # separate component: vertices 4-5
        ]
        print("[No valid stdin graph detected — running built-in demo graph]")

    result = minimum_spanning_forest(vertices, edges)
    print(f"Total cost: {result['total_cost']}")
    print(f"Selected edge IDs: {result['selected_edge_ids']}")


if __name__ == "__main__":
    main()