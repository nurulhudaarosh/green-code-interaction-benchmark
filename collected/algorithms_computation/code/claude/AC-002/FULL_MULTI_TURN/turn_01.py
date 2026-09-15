#!/usr/bin/env python3
"""
Deterministic Build Order Resolver
===================================

Problem
-------
Given a set of packages and a set of prerequisite (dependency) pairs, produce:
  1. A single, deterministic, valid build order in which every package is
     built only after all of its prerequisites have been built.
  2. The number of distinct "dependency levels" in that build — i.e. one
     more than the length of the longest prerequisite chain (a package
     with no prerequisites is at level 1).

If the dependency graph contains a cycle (no valid build order exists),
the function must return an empty order and -1 for the number of levels.

Key constraints
---------------
- Packages are identified by hashable, comparable values (this
  implementation assumes strings, but anything with a total order works).
- A prerequisite pair (pkg, prereq) means "prereq must be built before pkg".
- The result must be DETERMINISTIC: given the same input, the same build
  order must be produced every run, on every machine, regardless of
  dict/set iteration order or hashing. This rules out naive DFS/BFS with
  unordered sets and rules out relying on Python's dict insertion order
  alone when multiple packages are simultaneously buildable.
- No cycles allowed in a valid build; cycles must be detected, not just
  silently mishandled (e.g. by truncating output).
- Standard library only. No randomness, no network/API calls, no human
  interaction — the algorithm must be a pure function of its inputs.

Required output
----------------
- `order`: list[str]  -- the build order (empty list if a cycle exists).
- `levels`: int        -- number of dependency levels (-1 if a cycle exists).

Algorithm
---------
Kahn's algorithm for topological sorting, using a min-heap instead of a
plain queue/stack for the "frontier" of packages whose prerequisites are
all satisfied. Popping the lexicographically smallest ready package at
each step guarantees a unique, deterministic ordering among ties (which a
plain set/queue cannot guarantee, since insertion order into a set is not
well-defined and multiple packages can become ready simultaneously).

While relaxing edges, we also track `depth[pkg]`, the length of the
longest prerequisite chain ending at `pkg`:
    depth[pkg] = 0                                    if pkg has no prereqs
    depth[pkg] = max(depth[prereq] for prereq in ...) + 1   otherwise

This is computed incrementally and correctly under Kahn's algorithm
because a node's in-degree only reaches 0 (making it eligible for
processing/relaxation of its own outgoing edges) after *all* of its
prerequisites have already been popped and had their depths finalized.

The number of levels is `max(depth.values()) + 1` (levels are 1-indexed).

If, after the algorithm terminates, fewer packages have been ordered than
exist in the input, a cycle is present among the unordered packages, and
we return ([], -1).

Complexity: O((P + E) log P) where P = #packages, E = #prerequisite edges.
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
    levels for a package dependency graph.

    Parameters
    ----------
    packages:
        A sequence of distinct package identifiers (must be mutually
        comparable, e.g. all `str`, so heap tie-breaking is well-defined).
    prerequisites:
        A sequence of (package, prerequisite) pairs meaning `prerequisite`
        must be built before `package`. Duplicate pairs are tolerated.

    Returns
    -------
    (order, levels):
        order  -- deterministic list of all packages in valid build order,
                  or [] if a cycle is detected.
        levels -- number of dependency levels (longest chain length + 1),
                  or -1 if a cycle is detected.

    Raises
    ------
    ValueError
        If a prerequisite pair references a package not present in
        `packages`, or if `packages` contains duplicates.
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

    # Sort adjacency lists so that iteration order (used only for edge
    # relaxation, not for the heap itself) is deterministic too.
    for prereq in graph:
        graph[prereq].sort()

    depth: Dict[T, int] = {p: 0 for p in package_list}

    # Min-heap of currently "ready" packages (in-degree 0), ensuring we
    # always break ties deterministically by picking the smallest package.
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
                heapq.heappush(ready_heap, nxt)

    if len(order) != len(package_list):
        # Not all packages were ordered -> a cycle exists among the rest.
        return [], -1

    levels = (max(depth.values()) + 1) if package_list else 0
    return order, levels


def _demo() -> None:
    """Small self-contained demonstration / sanity check (no I/O, no
    randomness) run only when this file is executed directly."""

    print("Example 1: simple DAG")
    packages = ["a", "b", "c", "d", "e", "f"]
    prerequisites = [
        ("b", "a"),  # a before b
        ("c", "a"),  # a before c
        ("d", "b"),  # b before d
        ("d", "c"),  # c before d
        ("e", "d"),  # d before e
        ("f", "a"),  # a before f
    ]
    order, levels = build_order(packages, prerequisites)
    print("  order :", order)
    print("  levels:", levels)
    assert order == ["a", "b", "c", "f", "d", "e"], order
    assert levels == 4, levels

    print("Example 2: independent packages (single level)")
    packages2 = ["x", "y", "z"]
    order2, levels2 = build_order(packages2, [])
    print("  order :", order2)
    print("  levels:", levels2)
    assert order2 == ["x", "y", "z"], order2
    assert levels2 == 1, levels2

    print("Example 3: cycle detection")
    packages3 = ["p", "q", "r"]
    prerequisites3 = [("p", "q"), ("q", "r"), ("r", "p")]  # p<-q<-r<-p
    order3, levels3 = build_order(packages3, prerequisites3)
    print("  order :", order3)
    print("  levels:", levels3)
    assert order3 == [] and levels3 == -1

    print("\nAll checks passed.")


if __name__ == "__main__":
    _demo()