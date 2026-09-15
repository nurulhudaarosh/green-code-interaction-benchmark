"""
PROBLEM
=======
Given an undirected weighted graph (possibly disconnected), construct a
Minimum Spanning Forest (MSF) — i.e. a Minimum Spanning Tree for each
connected component — and return:
  1. The total cost (sum of weights) of the selected edges.
  2. The list of original edge IDs that were selected, in the order they
     were added to the forest.

KEY CONSTRAINTS
================
- The graph is undirected and weighted; it may be disconnected, so the
  result is a *forest* (one tree per component), not necessarily a
  single tree.
- Each edge has a unique original ID (its input index/position) that
  must be preserved in the output regardless of any internal sorting.
- Determinism: when multiple edges have equal weight, they must be
  considered in ascending order of their original edge ID. This ensures
  a single, reproducible answer instead of one dependent on unstable
  sort behavior or dict/set iteration order.
- No self-loops should be allowed to affect connectivity accounting in
  a broken way; self-loops (u == v) can never be part of a spanning
  forest and should simply be skipped.
- Parallel edges (multiple edges between the same pair of nodes) are
  allowed as input; only the cheapest useful ones will naturally be
  picked by Kruskal's algorithm.
- No randomness, no external I/O/network — pure, deterministic,
  standard-library-only computation.

REQUIRED OUTPUT
================
A tuple (total_cost, selected_edge_ids):
  - total_cost: int/float sum of weights of edges chosen for the MSF.
  - selected_edge_ids: list of original edge IDs chosen, in the order
    they were added while running Kruskal's algorithm.

ALGORITHM (Kruskal's with Disjoint Set Union)
==============================================
1. Assign each input edge its original ID (its index in the input list,
   unless explicit IDs are already given).
2. Sort all edges by (weight, original_id) ascending — the tie-break on
   ID guarantees determinism.
3. Initialize a Disjoint Set Union (Union-Find) structure over all
   vertices, using union by rank/size and path compression for
   near-O(1) amortized operations.
4. Iterate edges in sorted order. For each edge (u, v, w, id):
     - Skip if u == v (self-loop).
     - If find(u) != find(v): they are in different components, so
       union them, add w to total_cost, and record id as selected.
     - Otherwise skip (would form a cycle).
5. Stop early once (num_vertices - num_components) edges have been
   chosen (i.e., the forest already spans all components), or simply
   exhaust the sorted edge list — both give the same correct result.
6. Return total_cost and the list of selected original edge IDs.

Complexity: O(E log E) for sorting + O(E * alpha(V)) for DSU operations,
where alpha is the inverse Ackermann function (effectively constant).
"""

from typing import List, Tuple, Sequence, Hashable, Union


class DSU:
    """Disjoint Set Union (Union-Find) with path compression and union by rank."""

    def __init__(self, vertices: Sequence[Hashable]):
        self.parent = {v: v for v in vertices}
        self.rank = {v: 0 for v in vertices}

    def find(self, x: Hashable) -> Hashable:
        # Path compression (iterative to avoid recursion limits on large graphs).
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: Hashable, b: Hashable) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False  # already connected -> would form a cycle
        # Union by rank.
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def minimum_spanning_forest(
    vertices: Sequence[Hashable],
    edges: Sequence[Tuple[Hashable, Hashable, Union[int, float]]],
) -> Tuple[Union[int, float], List[int]]:
    """
    Compute a deterministic Minimum Spanning Forest via Kruskal's algorithm.

    Parameters
    ----------
    vertices : sequence of hashable vertex labels (all vertices in the graph,
               including isolated ones).
    edges    : sequence of (u, v, weight) tuples. The original edge ID of
               edges[i] is taken to be its index i in this sequence.

    Returns
    -------
    (total_cost, selected_edge_ids)
        total_cost         : sum of weights of the selected MSF edges.
        selected_edge_ids  : original indices of selected edges, in the
                              order they were added to the forest.
    """
    # Attach original IDs (their position in the input list) to each edge.
    indexed_edges = [
        (w, edge_id, u, v) for edge_id, (u, v, w) in enumerate(edges)
    ]

    # Deterministic ordering: ascending weight, then ascending original ID.
    indexed_edges.sort(key=lambda e: (e[0], e[1]))

    dsu = DSU(vertices)

    total_cost: Union[int, float] = 0
    selected_edge_ids: List[int] = []

    num_components_remaining = len(set(vertices))
    if num_components_remaining == 0:
        return 0, []

    for w, edge_id, u, v in indexed_edges:
        if u == v:
            continue  # skip self-loops; they can't help connectivity
        if dsu.union(u, v):
            total_cost += w
            selected_edge_ids.append(edge_id)
            num_components_remaining -= 1
            if num_components_remaining == 1:
                # All vertices in the graph are now in a single tree;
                # remaining edges (if it were one component) can't help.
                # NOTE: with multiple original components this just means
                # we've merged everything possible; loop naturally ends
                # once no more union() calls succeed anyway.
                pass

    return total_cost, selected_edge_ids


def _demo():
    # Example graph:
    #   Vertices: 0..5
    #   Component A: 0-1-2-3 (with a cycle and a tie in weights)
    #   Component B: 4-5 (separate component -> forest, not a single tree)
    vertices = [0, 1, 2, 3, 4, 5]
    edges = [
        (0, 1, 4),   # id 0
        (1, 2, 4),   # id 1  (tie with id 0's weight -> broken by id order)
        (2, 3, 1),   # id 2
        (0, 3, 5),   # id 3
        (0, 2, 2),   # id 4
        (4, 5, 3),   # id 5
        (1, 3, 4),   # id 6  (another tie at weight 4)
        (2, 2, 100), # id 7  self-loop, must be skipped
    ]

    total_cost, selected = minimum_spanning_forest(vertices, edges)
    print("Total cost:", total_cost)
    print("Selected original edge IDs:", selected)

    # Expected reasoning:
    # Sorted by (weight, id): (1,id2),(2,id4),(3,id5),(4,id0),(4,id1),(4,id6),(5,id3),(100,id7)
    # - id2 (2-3, w1): union -> cost=1, selected=[2]
    # - id4 (0-2, w2): union -> cost=3, selected=[2,4]
    # - id5 (4-5, w3): union -> cost=6, selected=[2,4,5]
    # - id0 (0-1, w4): union -> cost=10, selected=[2,4,5,0]
    # - id1 (1-2, w4): 1 and 2 already connected -> skip
    # - id6 (1-3, w4): already connected -> skip
    # - id3 (0-3, w5): already connected -> skip
    # - id7 self-loop -> skip
    # Final: total_cost = 10, selected = [2, 4, 5, 0]


if __name__ == "__main__":
    _demo()