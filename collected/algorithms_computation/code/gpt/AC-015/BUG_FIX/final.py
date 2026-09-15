"""
Maximum Flow Planner
====================

Problem Restatement
-------------------
Given a directed capacitated network, a source s, and a sink t, compute:

1. The maximum possible flow from s to t.
2. The flow assigned to every original edge.

The required behavior is:

- Use Dinic's blocking-flow algorithm.
- Preserve the exact original edge order in `edge_flows`.
- Handle parallel edges independently.
- Return exactly the required result fields.
- Keep the result deterministic: the same input must always produce the same
  output.
- Do not introduce unrelated output fields or change unrelated requirements.

Required Output
---------------
{
    "max_flow": <maximum s-t flow>,
    "edge_flows": [flow_for_original_edge_0,
                   flow_for_original_edge_1,
                   ...]
}

Bug Demonstration
-----------------
A common implementation defect is to reconstruct flows by looking only at
vertex pairs, for example:

    flow[(u, v)] = ...

This is incorrect when parallel edges exist because multiple original edges
can have the same `(u, v)` pair. Their flows can then be merged, overwritten,
or returned in the wrong positions.

Small valid counterexample:

    vertices: 0, 1, 2
    source = 0
    sink = 2

    original edges, in order:
        0: (0, 1, 2)
        1: (0, 1, 3)
        2: (1, 2, 4)

The maximum flow is 4.

A buggy pair-based reconstruction may report:

    edge_flows = [4, 0, 4]

or:

    edge_flows = [0, 4, 4]

Both are possible depending on how the `(0, 1)` pair is overwritten.

Neither is guaranteed to preserve the actual original-edge flow assignment
produced by the residual graph.

The correct implementation must keep a direct reference to EACH original
forward residual edge. Therefore the two parallel edges remain distinct and
their flows are returned in their original positions.

For this example, deterministic Dinic traversal produces:

    max_flow   = 4
    edge_flows = [2, 2, 4]

Algorithm
---------
Dinic's algorithm has two main phases:

1. BFS:
   Construct a level graph using only residual edges with positive capacity.
   Vertices are assigned their shortest residual distance from the source.

2. Blocking-flow DFS:
   Send flow only from a vertex at level d to a vertex at level d + 1.
   Continue until the current level graph has no more augmenting flow.

Repeat these phases until the sink is unreachable.

For deterministic behavior:
- Adjacency lists are built in original insertion order.
- DFS scans edges in that fixed order.
- `next_edge` remembers the next unused outgoing residual edge.
- Every original edge stores `(u, forward_edge_index, original_capacity)`.
- Final flow is:
      original_capacity - remaining_forward_capacity

Because the original-edge references are stored in input order, the returned
`edge_flows` list always has exactly the same order as the input.

Complexity
----------
For a general network, Dinic's algorithm runs in O(V^2 E) in the standard
general bound, where V is the number of vertices and E is the number of
residual/original edges up to constant-factor representation.

Implementation
--------------
"""

from collections import deque


def maximum_flow_planner(n, edges, source, sink):
    """
    Compute maximum s-t flow using Dinic's blocking-flow algorithm.

    Parameters
    ----------
    n : int
        Number of vertices, numbered 0 through n-1.

    edges : list[tuple[int, int, int]]
        Original directed edges in their required output order.
        Each edge is (u, v, capacity).

    source : int
        Source vertex.

    sink : int
        Sink vertex.

    Returns
    -------
    dict
        Exactly:
        {
            "max_flow": int,
            "edge_flows": list[int]
        }
    """

    if n < 0:
        raise ValueError("Number of vertices cannot be negative.")

    if not (0 <= source < n):
        raise ValueError("Source must be a valid vertex.")

    if not (0 <= sink < n):
        raise ValueError("Sink must be a valid vertex.")

    if source == sink:
        raise ValueError("Source and sink must be different.")

    # Each residual edge is:
    # [to, residual_capacity, reverse_index]
    graph = [[] for _ in range(n)]

    # IMPORTANT:
    # Store one reference for every original edge, in the exact input order.
    #
    # (u, index_in_graph_u, original_capacity)
    original_refs = []

    def add_residual_edge(u, v, capacity):
        forward_index = len(graph[u])

        # For a normal edge u != v, the reverse edge will be the next item
        # in graph[v].
        reverse_index = len(graph[v])

        # For a self-loop, both residual edges are inserted into graph[u].
        # Therefore the forward edge's reverse index must skip over itself.
        if u == v:
            reverse_index += 1

        graph[u].append([v, capacity, reverse_index])
        graph[v].append([u, 0, forward_index])

        return forward_index

    # Build the residual graph.
    #
    # Iterating through `edges` directly guarantees that all original
    # references are recorded in original order.
    for u, v, capacity in edges:
        if not (0 <= u < n) or not (0 <= v < n):
            raise ValueError("Edge endpoint is outside the valid range.")

        if capacity < 0:
            raise ValueError("Edge capacity cannot be negative.")

        forward_index = add_residual_edge(u, v, capacity)

        original_refs.append(
            (u, forward_index, capacity)
        )

    level = [-1] * n
    next_edge = [0] * n

    def build_level_graph():
        """
        Build the level graph with BFS.

        Only residual edges with positive capacity are usable.
        """
        for vertex in range(n):
            level[vertex] = -1

        level[source] = 0
        queue = deque([source])

        while queue:
            u = queue.popleft()

            for v, capacity, _ in graph[u]:
                if capacity > 0 and level[v] == -1:
                    level[v] = level[u] + 1
                    queue.append(v)

        return level[sink] != -1

    def blocking_flow(u, amount):
        """
        DFS used to send flow through the current level graph.

        The adjacency order never changes, making traversal deterministic.
        """
        if u == sink:
            return amount

        while next_edge[u] < len(graph[u]):
            edge_index = next_edge[u]
            edge = graph[u][edge_index]

            v = edge[0]
            capacity = edge[1]
            reverse_index = edge[2]

            if capacity > 0 and level[v] == level[u] + 1:
                pushed = blocking_flow(
                    v,
                    min(amount, capacity)
                )

                if pushed > 0:
                    # Decrease forward residual capacity.
                    edge[1] -= pushed

                    # Increase reverse residual capacity.
                    graph[v][reverse_index][1] += pushed

                    return pushed

            # This edge cannot contribute any more flow in this blocking
            # flow, so permanently advance the pointer for this vertex.
            next_edge[u] += 1

        return 0

    total_flow = 0

    # Dinic's algorithm.
    while build_level_graph():

        # Start scanning every adjacency list from its first edge for the
        # newly constructed level graph.
        for vertex in range(n):
            next_edge[vertex] = 0

        while True:
            pushed = blocking_flow(source, float("inf"))

            if pushed == 0:
                break

            total_flow += pushed

    # Recover each ORIGINAL edge independently.
    #
    # This is the critical bug fix: reconstruction uses the stored residual
    # edge reference rather than grouping edges by (u, v).
    edge_flows = []

    for u, forward_index, original_capacity in original_refs:
        remaining_capacity = graph[u][forward_index][1]

        flow = original_capacity - remaining_capacity
        edge_flows.append(flow)

    return {
        "max_flow": total_flow,
        "edge_flows": edge_flows,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_parallel_edges_deterministic_order():
    """
    Regression test for the reported bug.

    There are two distinct original edges from 0 -> 1.
    They must remain separate in the output.
    """
    edges = [
        (0, 1, 2),  # original edge 0
        (0, 1, 3),  # original edge 1
        (1, 2, 4),  # original edge 2
    ]

    result = maximum_flow_planner(
        n=3,
        edges=edges,
        source=0,
        sink=2,
    )

    assert result == {
        "max_flow": 4,
        "edge_flows": [2, 2, 4],
    }


def test_original_edge_order_is_preserved():
    """
    Edge order must be preserved even when capacities and endpoints vary.
    """
    edges = [
        (0, 2, 7),
        (0, 1, 5),
        (1, 2, 5),
    ]

    result = maximum_flow_planner(
        3,
        edges,
        0,
        2,
    )

    assert result["max_flow"] == 10
    assert len(result["edge_flows"]) == len(edges)

    # The direct edge is saturated and the 0 -> 1 -> 2 path is saturated.
    assert result["edge_flows"] == [7, 3, 3]


def test_parallel_edges_with_unused_capacity():
    edges = [
        (0, 1, 5),
        (0, 1, 5),
        (1, 2, 6),
    ]

    result = maximum_flow_planner(
        3,
        edges,
        0,
        2,
    )

    assert result == {
        "max_flow": 6,
        "edge_flows": [5, 1, 6],
    }


def test_basic_network():
    edges = [
        (0, 1, 10),
        (0, 2, 5),
        (1, 2, 15),
        (1, 3, 10),
        (2, 3, 10),
    ]

    result = maximum_flow_planner(
        4,
        edges,
        0,
        3,
    )

    assert result["max_flow"] == 15
    assert result["edge_flows"] == [10, 5, 5, 10, 10]


def test_no_path():
    edges = [
        (0, 1, 10),
        (2, 3, 10),
    ]

    result = maximum_flow_planner(
        4,
        edges,
        0,
        3,
    )

    assert result == {
        "max_flow": 0,
        "edge_flows": [0, 0],
    }


def test_zero_capacity_edges():
    edges = [
        (0, 1, 0),
        (0, 2, 5),
        (2, 1, 5),
    ]

    result = maximum_flow_planner(
        3,
        edges,
        0,
        1,
    )

    assert result == {
        "max_flow": 5,
        "edge_flows": [0, 5, 5],
    }


def test_empty_edge_list():
    result = maximum_flow_planner(
        3,
        [],
        0,
        2,
    )

    assert result == {
        "max_flow": 0,
        "edge_flows": [],
    }


def test_single_edge():
    edges = [
        (0, 1, 7),
    ]

    result = maximum_flow_planner(
        2,
        edges,
        0,
        1,
    )

    assert result == {
        "max_flow": 7,
        "edge_flows": [7],
    }


def test_self_loop_does_not_create_s_t_flow():
    edges = [
        (0, 0, 100),
        (0, 1, 5),
        (1, 1, 50),
    ]

    result = maximum_flow_planner(
        2,
        edges,
        0,
        1,
    )

    assert result == {
        "max_flow": 5,
        "edge_flows": [0, 5, 0],
    }


def test_determinism():
    edges = [
        (0, 1, 8),
        (0, 1, 2),
        (1, 2, 6),
        (0, 2, 3),
    ]

    first = maximum_flow_planner(3, edges, 0, 2)
    second = maximum_flow_planner(3, edges, 0, 2)

    assert first == second


def test_flow_never_exceeds_capacity():
    edges = [
        (0, 1, 8),
        (0, 2, 7),
        (1, 3, 5),
        (2, 3, 6),
        (1, 2, 4),
    ]

    result = maximum_flow_planner(
        4,
        edges,
        0,
        3,
    )

    assert result["max_flow"] == 11

    for flow, (_, _, capacity) in zip(result["edge_flows"], edges):
        assert 0 <= flow <= capacity


if __name__ == "__main__":
    # Demonstrate the bug-fixing example.
    demo_edges = [
        (0, 1, 2),
        (0, 1, 3),
        (1, 2, 4),
    ]

    print("Bug-fix demonstration:")
    print(maximum_flow_planner(3, demo_edges, 0, 2))

    # Run all regression tests.
    test_parallel_edges_deterministic_order()
    test_original_edge_order_is_preserved()
    test_parallel_edges_with_unused_capacity()
    test_basic_network()
    test_no_path()
    test_zero_capacity_edges()
    test_empty_edge_list()
    test_single_edge()
    test_self_loop_does_not_create_s_t_flow()
    test_determinism()
    test_flow_never_exceeds_capacity()

    print("All tests passed.")