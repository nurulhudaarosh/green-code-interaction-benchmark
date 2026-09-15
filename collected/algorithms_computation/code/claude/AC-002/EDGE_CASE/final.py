"""
Dependency Build Planner
=========================

Problem restatement
--------------------
Given:
  - a collection of package names, and
  - a collection of prerequisite dependency pairs (a, b) meaning
    "package a must be built before package b",

produce:
  1. A deterministic valid build order that includes every distinct
     package exactly once and respects every prerequisite constraint.
  2. The number of dependency levels: the length of the longest chain
     of prerequisites in the dependency graph (a lone package with no
     edges counts as 1 level; an empty package set counts as 0 levels).

If the dependency graph contains a cycle (including a package that is
listed as its own prerequisite), no valid build order exists, so the
function must return an empty build order and -1 as the level count.

Key constraints
----------------
- Determinism: identical input must always produce identical output,
  independent of dict/set iteration order, insertion order, or hashing.
  Ties among simultaneously-ready packages are broken lexicographically
  (smallest name first).
- Completeness: every distinct package named in `packages` or appearing
  in any dependency pair must appear exactly once in the output order.
- Robustness to repeated values (this revision's focus):
    * Duplicate entries in `packages` (e.g. ["A", "A", "B"]) must not
      create duplicate nodes, duplicate output entries, or inflated
      in-degrees.
    * Duplicate dependency pairs (e.g. [("A","B"), ("A","B")]) must not
      inflate `in_degree` counts — an edge is only ever counted once,
      regardless of how many times it is listed.
    * A self-referential dependency (e.g. ("A","A")) is a 1-node cycle
      and must be reported as a cycle (order = [], levels = -1), not
      silently ignored and not double-counted against A's in-degree.
- Cycle detection: any cycle (self-loop, 2-node, or longer) must result
  in ([], -1), never a partial order.
- No external/randomized/network/human-interaction behavior: pure,
  deterministic, standard-library-only computation.

Required output
----------------
A tuple (build_order, num_levels):
  - build_order: list[str] — deterministic topological order of all
    distinct packages, or [] if a cycle exists.
  - num_levels: int — length of the longest prerequisite chain, or -1
    if a cycle exists.

Algorithm
---------
Kahn's algorithm for topological sorting, using a min-heap (heapq)
instead of a plain queue/deque, so that whenever multiple packages
become "ready" (in-degree zero) simultaneously, the lexicographically
smallest one is always chosen next — giving one deterministic output
regardless of hash/set iteration order.

Repeated-value handling is folded directly into graph construction:
  - `packages` is first coerced into a `set` to collapse duplicates
    before any node/in-degree bookkeeping happens.
  - Each (prereq, package) edge is only added to the adjacency set if
    it is not already present, and `in_degree[package]` is only
    incremented at the moment the edge is newly added — so listing the
    same edge N times has the same effect as listing it once.
  - A self-loop (prereq == package) is added as an edge like any other;
    because it can never resolve (the node depends on itself), it is
    naturally caught by the standard "not all nodes processed" cycle
    check at the end, without special-casing.

While popping nodes from the heap, each node's "depth" is tracked:
depth(node) = 0 if it has no prerequisites, otherwise
1 + max(depth(prereq) for prereq in its prerequisites), computed
incrementally via edge relaxation as nodes are popped in topological
order. The number of levels is 1 + max(depth) over all nodes, or 0 if
there are no packages at all.

If, after processing, not all distinct packages have been emitted, a
cycle exists among the remaining packages -> return ([], -1).

Complexity: O((V + E) log V) due to heap operations, where V and E are
counted over *distinct* nodes and edges after de-duplication.
"""

import heapq
from collections import defaultdict


def build_order(packages, dependencies):
    """
    Compute a deterministic build order and dependency level count.

    Args:
        packages: iterable of package name strings (may contain
            duplicates; duplicates are collapsed before processing).
            All packages that must appear in the build order, including
            isolated ones, should be included here.
        dependencies: iterable of (prereq, package) tuples meaning
            `prereq` must be built before `package`. May contain
            duplicate pairs and/or self-loops (prereq == package);
            both are handled explicitly (see module docstring).

    Returns:
        (order, num_levels):
            order: list[str] - deterministic topological build order,
                   or [] if a cycle is detected.
            num_levels: int - number of dependency levels (>=0 for a
                   valid DAG, 1 for a single node with no edges, 0 for
                   no packages at all), or -1 if a cycle is detected.
    """
    # De-duplicate packages up front so repeated entries never create
    # phantom nodes or inflate counts.
    all_packages = set(packages)

    graph = defaultdict(set)   # prereq -> set of dependents (deduped)
    in_degree = {pkg: 0 for pkg in all_packages}

    for prereq, package in dependencies:
        # Any package named only in `dependencies` still needs bookkeeping.
        if prereq not in all_packages:
            all_packages.add(prereq)
            in_degree[prereq] = 0
        if package not in all_packages:
            all_packages.add(package)
            in_degree[package] = 0

        # Only count a given edge once, no matter how many times the
        # same (prereq, package) pair — including a self-loop where
        # prereq == package — appears in `dependencies`.
        if package not in graph[prereq]:
            graph[prereq].add(package)
            in_degree[package] += 1

    if not all_packages:
        return [], 0

    depth = {pkg: 0 for pkg in all_packages}

    heap = sorted(pkg for pkg in all_packages if in_degree[pkg] == 0)
    heapq.heapify(heap)

    order = []
    visited_count = 0

    while heap:
        node = heapq.heappop(heap)
        order.append(node)
        visited_count += 1

        for neighbor in sorted(graph[node]):
            if depth[node] + 1 > depth[neighbor]:
                depth[neighbor] = depth[node] + 1
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    if visited_count != len(all_packages):
        # Cycle detected (includes self-loops): not all nodes could be
        # fully resolved because some remain with in_degree > 0 forever.
        return [], -1

    num_levels = max(depth.values()) + 1
    return order, num_levels


def _run_self_tests():
    # --- Original core-behavior tests (preserved) -------------------

    # Simple linear chain: A -> B -> C
    order, levels = build_order(
        ["A", "B", "C"], [("A", "B"), ("B", "C")]
    )
    assert order == ["A", "B", "C"], order
    assert levels == 3, levels

    # Diamond dependency: A -> B, A -> C, B -> D, C -> D
    order, levels = build_order(
        ["A", "B", "C", "D"],
        [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")],
    )
    assert order == ["A", "B", "C", "D"], order
    assert levels == 3, levels

    # Disconnected + isolated node, deterministic tie-break by name
    order, levels = build_order(
        ["X", "Y", "Z", "W"], [("Y", "Z")]
    )
    assert order == ["W", "X", "Y", "Z"], order
    assert levels == 2, levels

    # No packages at all
    order, levels = build_order([], [])
    assert order == [] and levels == 0

    # Single isolated package
    order, levels = build_order(["A"], [])
    assert order == ["A"] and levels == 1

    # Cycle: A -> B -> A
    order, levels = build_order(["A", "B"], [("A", "B"), ("B", "A")])
    assert order == [] and levels == -1

    # Larger cycle mixed with valid part: A->B->C->A, D independent
    order, levels = build_order(
        ["A", "B", "C", "D"],
        [("A", "B"), ("B", "C"), ("C", "A")],
    )
    assert order == [] and levels == -1

    # --- New tests: repeated values ----------------------------------

    # Duplicate package entries must collapse to one node, no effect
    # on order or levels versus the de-duplicated equivalent.
    order, levels = build_order(
        ["A", "A", "B", "B", "B", "C"],
        [("A", "B"), ("B", "C")],
    )
    assert order == ["A", "B", "C"], order
    assert levels == 3, levels

    # Duplicate dependency pairs must not inflate in-degree: B should
    # still become ready immediately after A is processed, not require
    # A to be "counted" multiple times.
    order, levels = build_order(
        ["A", "B"],
        [("A", "B"), ("A", "B"), ("A", "B")],
    )
    assert order == ["A", "B"], order
    assert levels == 2, levels

    # Duplicate edges mixed with an otherwise-valid diamond: repeating
    # one edge must not change the result versus the single-copy case.
    order, levels = build_order(
        ["A", "B", "C", "D"],
        [("A", "B"), ("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("C", "D")],
    )
    assert order == ["A", "B", "C", "D"], order
    assert levels == 3, levels

    # Self-loop is a 1-node cycle: must report ([], -1), not silently
    # treat A as buildable or double-penalize its in-degree.
    order, levels = build_order(["A"], [("A", "A")])
    assert order == [] and levels == -1

    # Self-loop on one node coexisting with an otherwise valid, separate
    # chain: the whole result must still be a cycle, because Kahn's
    # algorithm cannot fully drain a graph containing any cycle.
    order, levels = build_order(
        ["A", "B", "C"],
        [("A", "A"), ("B", "C")],
    )
    assert order == [] and levels == -1

    # Repeated self-loop entries: listing the same self-loop multiple
    # times must not change the outcome versus listing it once.
    order, levels = build_order(
        ["A", "B"],
        [("A", "A"), ("A", "A"), ("A", "B")],
    )
    assert order == [] and levels == -1

    # Deterministic ties: many isolated packages with no edges at all
    # must come out in strict lexicographic order.
    order, levels = build_order(
        ["delta", "bravo", "charlie", "alpha", "bravo", "alpha"], []
    )
    assert order == ["alpha", "bravo", "charlie", "delta"], order
    assert levels == 1, levels

    # Deterministic ties combined with repeated dependency declarations:
    # two independent chains that free up nodes at the same "round"
    # must interleave by lexicographic order at each tie point.
    #   A -> M, B -> N   (A, B ready initially; M, N ready after)
    order, levels = build_order(
        ["A", "B", "M", "N"],
        [("A", "M"), ("A", "M"), ("B", "N")],
    )
    assert order == ["A", "B", "M", "N"], order
    assert levels == 2, levels

    print("All self-tests passed.")


if __name__ == "__main__":
    _run_self_tests()

    demo_packages = ["libc", "compiler", "linker", "app", "utils", "libc"]
    demo_deps = [
        ("libc", "compiler"),
        ("libc", "linker"),
        ("compiler", "app"),
        ("linker", "app"),
        ("utils", "app"),
        ("libc", "compiler"),  # duplicate edge, should have no extra effect
    ]
    result_order, result_levels = build_order(demo_packages, demo_deps)
    print("Build order:", result_order)
    print("Levels:", result_levels)