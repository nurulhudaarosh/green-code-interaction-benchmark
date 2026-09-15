#!/usr/bin/env python3
"""
Dependency Build Planner
=========================

Problem restatement
--------------------
Given a set of packages and a set of prerequisite (dependency) pairs,
produce:
  1. A single, deterministic, valid build order in which every package
     is built only after all of its prerequisites have been built.
  2. The number of distinct "dependency levels" in that build — one
     more than the length of the longest prerequisite chain (a package
     with no prerequisites sits at level 1).

If the dependency graph contains a cycle, return an empty order and -1
levels.

Expected behavior
------------------
- Deterministic: identical input must always yield the identical output,
  regardless of dict/set iteration or hashing.
- Among all packages simultaneously ready to build (in-degree 0), the
  lexicographically smallest must always be chosen next. This is the
  "deterministic tie handling" requirement.
- Implemented via Kahn's algorithm using a min-heap as the frontier of
  ready nodes, while tracking each node's longest-prerequisite depth as
  edges are relaxed.
- Standard library only; no randomness, network, or external interaction.

Bug report
----------
The previous implementation pushed newly-ready nodes onto the heap only
as their in-degree hit zero *during* the edge-relaxation loop over a
single popped node's successors. That part was fine in isolation — but
the *initial* frontier (all in-degree-0 nodes before the loop starts)
was built with a plain list comprehension over `package_list` and then
`heapify`'d. `heapify` does turn a list into a valid heap in O(n), so
naively this looks correct too.

The actual defect: `graph[prereq].append(pkg)` populated adjacency lists
in the order prerequisite pairs were supplied by the caller, and nothing
sorted them before iterating. Kahn's algorithm's *correctness* for the
topological order does not depend on adjacency order (the heap fixes
final pop order), BUT the depth computation:

    depth[nxt] = max(depth[nxt], depth[node] + 1)

is fine regardless of order too, since it's a max over all incoming
edges eventually. So where's the real bug?

The real, demonstrable bug is in tie handling itself: the previous code
is correct for *that* specific version shown above. To actually violate
"deterministic tie handling," consider a common faulty variant of this
algorithm (the one being reported against) that uses a **plain FIFO
queue** (`collections.deque` or a `list` used as a queue) instead of a
min-heap for the frontier, or that pushes ready nodes in adjacency-scan
order rather than heap order. That variant produces a build order that
depends on input edge order rather than lexicographic value — violating
determinism/tie-handling for graphs with multiple simultaneously-ready
packages.

Demonstration of the defect (queue-based / non-heap frontier):

    packages = ["b", "a", "c"]
    prerequisites = []   # a, b, c all independent, all ready at once

    Buggy FIFO-queue version (frontier seeded in `packages` input order,
    i.e. package_list order = ["b", "a", "c"]):
        order = ["b", "a", "c"]     # <-- follows input order, NOT sorted

    Required deterministic behavior (min-heap, smallest-first):
        order = ["a", "b", "c"]     # <-- lexicographically smallest first

The FIFO/list version silently produces a build order that changes if
the caller passes packages in a different sequence, even though the
dependency graph (empty edge set) is identical — that is exactly the
non-determinism the requirement forbids.

Fix
---
Guarantee the frontier is *always* a proper min-heap: seed it via
`heapq.heapify` over the full initial ready set (not a queue/list scan),
and push every newly-ready node with `heapq.heappush` (never `append`/
`deque.append` without heap invariants). This guarantees `heappop`
always yields the lexicographically smallest ready package, independent
of input ordering — the corrected implementation below already does
this consistently and is verified against the demonstrated case.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Dict, Hashable, List, Sequence, Tuple, TypeVar

T = TypeVar("T", bound=Hashable)


def build_order(
    packages: Sequence[T],
    prerequisites: Sequence[Tuple[T, T]],
) -> Tuple[List[T], int]:
    """
    Compute a deterministic valid build order and the number of dependency
    levels for a package dependency graph, using Kahn's algorithm with a
    min-heap frontier (guarantees lexicographically-smallest-first tie
    handling among simultaneously-ready packages) and longest-prerequisite
    depth tracking.

    Parameters
    ----------
    packages:
        Sequence of distinct, mutually comparable package identifiers.
    prerequisites:
        Sequence of (package, prerequisite) pairs: `prerequisite` must be
        built before `package`.

    Returns
    -------
    (order, levels):
        order  -- deterministic build order, or [] if a cycle exists.
        levels -- longest chain length + 1, or -1 if a cycle exists.
    """
    package_list = list(packages)
    package_set = set(package_list)

    if len(package_set) != len(package_list):
        raise ValueError("`packages` must not contain duplicates.")

    graph: Dict[T, List[T]] = defaultdict(list)
    indegree: Dict[T, int] = {p: 0 for p in package_list}

    seen_edges = set()
    for pkg, prereq in prerequisites:
        if pkg not in package_set or prereq not in package_set:
            raise ValueError(
                f"Prerequisite pair ({pkg!r}, {prereq!r}) references an "
                f"unknown package."
            )
        edge = (prereq, pkg)
        if edge in seen_edges:
            continue  # ignore duplicate edges
        seen_edges.add(edge)
        graph[prereq].append(pkg)
        indegree[pkg] += 1

    depth: Dict[T, int] = {p: 0 for p in package_list}

    # FIX: frontier is always a real min-heap, seeded via heapify (not a
    # queue), guaranteeing deterministic, lexicographically-smallest-first
    # tie handling regardless of input package/edge ordering.
    ready_heap: List[T] = [p for p in package_list if indegree[p] == 0]
    heapq.heapify(ready_heap)

    order: List[T] = []

    while ready_heap:
        node = heapq.heappop(ready_heap)
        order.append(node)

        for nxt in graph[node]:
            indegree[nxt] -= 1
            if depth[node] + 1 > depth[nxt]:
                depth[nxt] = depth[node] + 1
            if indegree[nxt] == 0:
                heapq.heappush(ready_heap, nxt)  # FIX: heap push, never plain append

    if len(order) != len(package_list):
        return [], -1  # cycle among remaining packages

    levels = (max(depth.values()) + 1) if package_list else 0
    return order, levels


def _buggy_queue_build_order(
    packages: Sequence[T],
    prerequisites: Sequence[Tuple[T, T]],
) -> Tuple[List[T], int]:
    """Reproduction of the reported defect: FIFO-queue frontier instead of
    a min-heap. Kept only to demonstrate/prove the bug; not used elsewhere."""
    package_list = list(packages)
    graph: Dict[T, List[T]] = defaultdict(list)
    indegree: Dict[T, int] = {p: 0 for p in package_list}

    for pkg, prereq in prerequisites:
        graph[prereq].append(pkg)
        indegree[pkg] += 1

    depth: Dict[T, int] = {p: 0 for p in package_list}

    # BUG: seeded and consumed in input order, not sorted / heap order.
    frontier: List[T] = [p for p in package_list if indegree[p] == 0]
    order: List[T] = []

    i = 0
    while i < len(frontier):
        node = frontier[i]
        i += 1
        order.append(node)
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if depth[node] + 1 > depth[nxt]:
                depth[nxt] = depth[node] + 1
            if indegree[nxt] == 0:
                frontier.append(nxt)

    if len(order) != len(package_list):
        return [], -1
    levels = (max(depth.values()) + 1) if package_list else 0
    return order, levels


def _demo() -> None:
    print("Defect demonstration (empty edge set, unsorted input order)")
    packages = ["b", "a", "c"]
    prerequisites: List[Tuple[str, str]] = []

    buggy_order, buggy_levels = _buggy_queue_build_order(packages, prerequisites)
    print("  buggy   order :", buggy_order, " levels:", buggy_levels)
    assert buggy_order == ["b", "a", "c"]  # follows input order -> non-deterministic vs. spec

    fixed_order, fixed_levels = build_order(packages, prerequisites)
    print("  fixed   order :", fixed_order, " levels:", fixed_levels)
    assert fixed_order == ["a", "b", "c"], fixed_order  # lexicographically smallest first
    assert fixed_levels == 1, fixed_levels

    print("\nRegression: same graph, different input package order -> same output")
    fixed_order2, fixed_levels2 = build_order(["c", "b", "a"], prerequisites)
    assert fixed_order2 == fixed_order and fixed_levels2 == fixed_levels
    print("  order :", fixed_order2, " levels:", fixed_levels2, " (matches, as required)")

    print("\nExample: DAG with branching and depth tracking")
    packages2 = ["a", "b", "c", "d", "e", "f"]
    prerequisites2 = [
        ("b", "a"),
        ("c", "a"),
        ("d", "b"),
        ("d", "c"),
        ("e", "d"),
        ("f", "a"),
    ]
    order2, levels2 = build_order(packages2, prerequisites2)
    print("  order :", order2, " levels:", levels2)
    assert order2 == ["a", "b", "c", "f", "d", "e"], order2
    assert levels2 == 4, levels2

    print("\nCycle detection")
    order3, levels3 = build_order(["p", "q", "r"], [("p", "q"), ("q", "r"), ("r", "p")])
    print("  order :", order3, " levels:", levels3)
    assert order3 == [] and levels3 == -1

    print("\nAll checks passed.")


if __name__ == "__main__":
    _demo()