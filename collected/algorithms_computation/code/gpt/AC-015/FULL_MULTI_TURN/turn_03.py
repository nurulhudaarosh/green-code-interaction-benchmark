"""
Maximum Flow Planner — operation_summary feature
=================================================

PROBLEM RESTATEMENT
-------------------
Given a directed capacitated network, a source vertex s, and a sink
vertex t, compute the maximum possible flow from s to t.

The planner must also report the flow carried by every ORIGINAL edge,
with those flows appearing in exactly the same order as the input edges.

EXISTING REQUIRED OUTPUT
------------------------
The original result is:

{
    "max_flow": <maximum s-t flow>,
    "edge_flows": [<flow of edge 0>, <flow of edge 1>, ...]
}

Requirements that remain unchanged:
- Use Dinic's blocking-flow algorithm.
- The graph is directed.
- Capacities are non-negative.
- Parallel edges are allowed.
- Every edge flow must remain within its capacity.
- `edge_flows` must preserve original input-edge order.
- Edge identity must be preserved even for parallel edges.
- Processing must be deterministic.
- Standard library only.
- No network, APIs, external services, randomness, or human interaction.
- The result must contain exactly the original fields when the new
  feature is disabled or not requested.

NEW FEATURE
-----------
When `include_operation_summary=True`, add:

    "operation_summary": {
        "bfs_level_graph_builds": ...,
        "dfs_blocking_flow_calls": ...,
        "successful_flow_augmentations": ...,
        "edge_scans": ...
    }

The values are deterministic counts of major computational
decisions/operations made by Dinic's algorithm.

Definitions:
- bfs_level_graph_builds:
    Number of BFS phases used to construct level graphs.

- dfs_blocking_flow_calls:
    Number of DFS calls made while constructing blocking flows,
    including calls that return zero flow.

- successful_flow_augmentations:
    Number of DFS calls that successfully push positive flow from
    source to sink.

- edge_scans:
    Number of residual edges examined by BFS and DFS.

These counters depend only on the fixed deterministic adjacency
order and therefore provide a reproducible operation summary.

IMPORTANT:
If `include_operation_summary=False` (the default), the returned
dictionary remains exactly:

    {
        "max_flow": ...,
        "edge_flows": [...]
    }

No operation_summary field is added.

ALGORITHM
---------
Dinic's algorithm repeatedly:

1. Runs BFS from s to construct a level graph.
2. Uses DFS to send a blocking flow through edges that move exactly
   one level forward.
3. Repeats until t is unreachable.

For every original edge we store the exact forward residual-edge
index. Therefore, after Dinic finishes:

    flow = original_capacity - remaining_forward_capacity

and the flows can be reconstructed in original input order.

Deterministic behavior:
- Adjacency lists are populated in input order.
- BFS scans adjacency lists in insertion order.
- DFS scans adjacency lists in insertion order.
- No sets, unordered traversal, or randomness are used.
"""

from collections import deque


class Dinic:
    def __init__(self, n, include_operation_summary=False):
        self.n = n
        self.graph = [[] for _ in range(n)]

        # Each item:
        # (u, v, original_capacity, forward_edge_index)
        #
        # This list always remains in original input order.
        self.original_edges = []

        self.include_operation_summary = include_operation_summary

        # Deterministic operation counters.
        self.bfs_level_graph_builds = 0
        self.dfs_blocking_flow_calls = 0
        self.successful_flow_augmentations = 0
        self.edge_scans = 0

    def add_edge(self, u, v, capacity):
        if capacity < 0:
            raise ValueError("Capacity must be non-negative.")

        forward_index = len(self.graph[u])
        reverse_index = len(self.graph[v])

        # [to, residual_capacity, reverse_edge_index]
        forward = [v, capacity, reverse_index]
        reverse = [u, 0, forward_index]

        self.graph[u].append(forward)
        self.graph[v].append(reverse)

        # Store a stable reference to this ORIGINAL edge.
        self.original_edges.append(
            (u, v, capacity, forward_index)
        )

    def _build_level_graph(self, source, sink):
        self.bfs_level_graph_builds += 1

        self.level = [-1] * self.n
        self.level[source] = 0

        queue = deque([source])

        while queue:
            u = queue.popleft()

            for edge in self.graph[u]:
                self.edge_scans += 1

                v, capacity, _ = edge

                if capacity > 0 and self.level[v] == -1:
                    self.level[v] = self.level[u] + 1
                    queue.append(v)

        return self.level[sink] != -1

    def _send_blocking_flow(self, u, sink, pushed):
        self.dfs_blocking_flow_calls += 1

        if u == sink:
            self.successful_flow_augmentations += 1
            return pushed

        while self.pointer[u] < len(self.graph[u]):
            edge_index = self.pointer[u]
            edge = self.graph[u][edge_index]

            self.edge_scans += 1

            v, capacity, reverse_index = edge

            if (
                capacity > 0
                and self.level[v] == self.level[u] + 1
            ):
                flow = self._send_blocking_flow(
                    v,
                    sink,
                    min(pushed, capacity)
                )

                if flow > 0:
                    edge[1] -= flow
                    self.graph[v][reverse_index][1] += flow
                    return flow

            # This edge cannot currently contribute to the blocking
            # flow, so advance the current-arc pointer.
            self.pointer[u] += 1

        return 0

    def max_flow(self, source, sink):
        if not (0 <= source < self.n):
            raise ValueError("Invalid source vertex.")

        if not (0 <= sink < self.n):
            raise ValueError("Invalid sink vertex.")

        if source == sink:
            return 0

        total_flow = 0
        infinity = 10**30

        while self._build_level_graph(source, sink):
            self.pointer = [0] * self.n

            while True:
                pushed = self._send_blocking_flow(
                    source,
                    sink,
                    infinity
                )

                if pushed == 0:
                    break

                total_flow += pushed

        return total_flow

    def get_original_edge_flows(self):
        """
        Recover flows strictly in original input order.
        """
        flows = []

        for u, v, original_capacity, forward_index in self.original_edges:
            remaining_capacity = self.graph[u][forward_index][1]
            flow = original_capacity - remaining_capacity
            flows.append(flow)

        return flows

    def get_operation_summary(self):
        return {
            "bfs_level_graph_builds": self.bfs_level_graph_builds,
            "dfs_blocking_flow_calls": self.dfs_blocking_flow_calls,
            "successful_flow_augmentations": (
                self.successful_flow_augmentations
            ),
            "edge_scans": self.edge_scans,
        }


def maximum_flow_planner(
    n,
    edges,
    source,
    sink,
    include_operation_summary=False
):
    """
    Compute a maximum s-t flow using deterministic Dinic.

    Parameters
    ----------
    n:
        Number of vertices, numbered 0 through n-1.

    edges:
        List of (u, v, capacity) tuples in original input order.

    source:
        Source vertex.

    sink:
        Sink vertex.

    include_operation_summary:
        If True, add the deterministic operation_summary field.

    Returns
    -------
    When disabled (default):
        {
            "max_flow": ...,
            "edge_flows": [...]
        }

    When enabled:
        {
            "max_flow": ...,
            "edge_flows": [...],
            "operation_summary": {...}
        }
    """

    if n < 0:
        raise ValueError("Number of vertices cannot be negative.")

    if not (0 <= source < n):
        raise ValueError("Invalid source vertex.")

    if not (0 <= sink < n):
        raise ValueError("Invalid sink vertex.")

    dinic = Dinic(
        n,
        include_operation_summary=include_operation_summary
    )

    for u, v, capacity in edges:
        if not (0 <= u < n):
            raise ValueError("Invalid edge source vertex.")

        if not (0 <= v < n):
            raise ValueError("Invalid edge destination vertex.")

        if capacity < 0:
            raise ValueError("Capacity must be non-negative.")

        dinic.add_edge(u, v, capacity)

    maximum = dinic.max_flow(source, sink)

    result = {
        "max_flow": maximum,
        "edge_flows": dinic.get_original_edge_flows(),
    }

    # The original output is completely unchanged when this feature
    # is disabled.
    if include_operation_summary:
        result["operation_summary"] = (
            dinic.get_operation_summary()
        )

    return result


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def run_tests():
    # Test 1:
    # Original edge order is deliberately different from vertex order.
    edges = [
        (2, 3, 7),   # original edge 0
        (0, 2, 7),   # original edge 1
        (0, 1, 5),   # original edge 2
        (1, 3, 5),   # original edge 3
    ]

    result = maximum_flow_planner(
        4,
        edges,
        source=0,
        sink=3
    )

    assert result == {
        "max_flow": 12,
        "edge_flows": [7, 7, 5, 5],
    }

    # Test 2:
    # Parallel edges remain separate and retain their original order.
    edges = [
        (0, 1, 3),
        (0, 1, 7),
    ]

    result = maximum_flow_planner(
        2,
        edges,
        source=0,
        sink=1
    )

    assert result == {
        "max_flow": 10,
        "edge_flows": [3, 7],
    }

    # Test 3:
    # No path from source to sink.
    result = maximum_flow_planner(
        4,
        [
            (0, 1, 10),
            (2, 3, 20),
        ],
        source=0,
        sink=3
    )

    assert result == {
        "max_flow": 0,
        "edge_flows": [0, 0],
    }

    # Test 4:
    # Zero-capacity edge.
    result = maximum_flow_planner(
        3,
        [
            (0, 1, 0),
            (1, 2, 10),
        ],
        source=0,
        sink=2
    )

    assert result == {
        "max_flow": 0,
        "edge_flows": [0, 0],
    }

    # Test 5:
    # Multiple paths.
    result = maximum_flow_planner(
        4,
        [
            (0, 1, 10),
            (0, 2, 10),
            (1, 3, 4),
            (2, 3, 6),
        ],
        source=0,
        sink=3
    )

    assert result == {
        "max_flow": 10,
        "edge_flows": [4, 6, 4, 6],
    }

    # Test 6:
    # Residual rerouting is supported.
    edges = [
        (0, 1, 10),
        (0, 2, 10),
        (1, 2, 10),
        (1, 3, 10),
        (2, 3, 10),
    ]

    result = maximum_flow_planner(
        4,
        edges,
        source=0,
        sink=3
    )

    assert result["max_flow"] == 20

    for edge, flow in zip(edges, result["edge_flows"]):
        assert 0 <= flow <= edge[2]

    # Test 7:
    # Source equals sink.
    result = maximum_flow_planner(
        3,
        [
            (0, 1, 5),
            (1, 2, 5),
        ],
        source=1,
        sink=1
    )

    assert result == {
        "max_flow": 0,
        "edge_flows": [0, 0],
    }

    # Test 8:
    # Empty graph.
    result = maximum_flow_planner(
        3,
        [],
        source=0,
        sink=2
    )

    assert result == {
        "max_flow": 0,
        "edge_flows": [],
    }

    # Test 9:
    # Critical requirement:
    # when the feature is disabled, NO new field is returned.
    result = maximum_flow_planner(
        2,
        [(0, 1, 5)],
        source=0,
        sink=1,
        include_operation_summary=False
    )

    assert list(result.keys()) == [
        "max_flow",
        "edge_flows",
    ]

    # Test 10:
    # operation_summary is present only when requested.
    result = maximum_flow_planner(
        4,
        [
            (0, 1, 5),
            (0, 2, 7),
            (1, 3, 5),
            (2, 3, 7),
        ],
        source=0,
        sink=3,
        include_operation_summary=True
    )

    assert result["max_flow"] == 12
    assert result["edge_flows"] == [5, 7, 5, 7]

    summary = result["operation_summary"]

    assert set(summary.keys()) == {
        "bfs_level_graph_builds",
        "dfs_blocking_flow_calls",
        "successful_flow_augmentations",
        "edge_scans",
    }

    assert summary["bfs_level_graph_builds"] > 0
    assert summary["dfs_blocking_flow_calls"] > 0
    assert summary["successful_flow_augmentations"] > 0
    assert summary["edge_scans"] > 0

    # Test 11:
    # Determinism: running the same input twice must produce exactly
    # the same complete result, including operation_summary.
    edges = [
        (0, 1, 10),
        (0, 2, 10),
        (1, 3, 4),
        (2, 3, 6),
    ]

    result_a = maximum_flow_planner(
        4,
        edges,
        source=0,
        sink=3,
        include_operation_summary=True
    )

    result_b = maximum_flow_planner(
        4,
        edges,
        source=0,
        sink=3,
        include_operation_summary=True
    )

    assert result_a == result_b

    # Test 12:
    # The operation summary does not change the actual flow result.
    without_summary = maximum_flow_planner(
        2,
        [(0, 1, 100)],
        source=0,
        sink=1
    )

    with_summary = maximum_flow_planner(
        2,
        [(0, 1, 100)],
        source=0,
        sink=1,
        include_operation_summary=True
    )

    assert with_summary["max_flow"] == without_summary["max_flow"]
    assert with_summary["edge_flows"] == without_summary["edge_flows"]

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()