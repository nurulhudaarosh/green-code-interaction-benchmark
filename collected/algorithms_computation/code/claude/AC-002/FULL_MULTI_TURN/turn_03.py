#!/usr/bin/env python3
"""
Dependency Build Planner
=========================

Problem restatement (original, unchanged)
-------------------------------------------
Given a set of packages and a set of prerequisite (dependency) pairs,
produce:
  1. A single, deterministic, valid build order in which every package
     is built only after all of its prerequisites have been built.
  2. The number of distinct "dependency levels" in that build — one
     more than the length of the longest prerequisite chain (a package
     with no prerequisites sits at level 1).

If the dependency graph contains a cycle, return an empty order and -1
levels.

Existing required outputs (unchanged)
---------------------------------------
- `order`: list[T]  -- deterministic build order, or [] if a cycle exists.
- `levels`: int     -- number of dependency levels, or -1 if a cycle exists.

Determinism requirement (unchanged): among all packages simultaneously
ready to build (in-degree 0), the lexicographically smallest is always
chosen next — enforced via Kahn's algorithm with a min-heap frontier,
seeded and updated exclusively through `heapq.heapify`/`heapq.heappush`
(never a plain queue/list scan), while longest-prerequisite `depth` is
tracked incrementally as edges are relaxed. Standard library only; no
randomness, network, or external interaction.

New feature: `operation_summary`
----------------------------------
When explicitly requested (via `include_summary=True`), the function
additionally returns a third field, `operation_summary`: a dict reporting
a deterministic count of the major computational decisions/operations the
algorithm performed while producing `order`/`levels`. Specifically:

- `heap_pops`        : number of times a package was popped as "next to
                        build" (equals `len(order)` on success).
- `heap_pushes`       : number of times a package became ready and was
                        pushed onto the frontier heap (initial seeding +
                        newly-ready pushes during relaxation).
- `edge_relaxations`  : number of prerequisite edges actually relaxed
                        (in-degree decremented), i.e. the number of
                        (prereq -> pkg) edges processed.
- `depth_updates`     : number of times an edge relaxation *improved* a
                        node's recorded longest-prerequisite depth.
- `cycle_detected`    : bool, whether a cycle was found.

This is purely additive:
- When `include_summary` is False (the default), the function returns
  exactly the original 2-tuple `(order, levels)` — byte-for-byte the same
  contract as before. No existing field, type, or behavior changes.
- When `include_summary` is True, it returns the 3-tuple
  `(order, levels, operation_summary)`; `order` and `levels` are computed
  identically to the disabled case.
- `operation_summary` counts are derived deterministically from the same
  single deterministic run of the algorithm (no extra randomness, no
  second differently-ordered pass), so repeated calls with identical
  input always produce an identical summary.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Dict, Hashable, List, Sequence, Tuple, TypeVar, Union

T = TypeVar("T", bound=Hashable)

OperationSummary = Dict[str, Union[int, bool]]


def build_order(
    packages: Sequence[T],
    prerequisites: Sequence[Tuple[T, T]],
    include_summary: bool = False,
) -> Union[Tuple[List[T], int], Tuple[List[T], int, OperationSummary]]:
    """
    Compute a deterministic valid build order and the number of dependency
    levels for a package dependency graph, using Kahn's algorithm with a
    min-heap frontier (guaranteeing lexicographically-smallest-first tie
    handling among simultaneously-ready packages) and longest-prerequisite
    depth tracking.

    Parameters
    ----------
    packages:
        Sequence of distinct, mutually comparable package identifiers.
    prerequisites:
        Sequence of (package, prerequisite) pairs: `prerequisite` must be
        built before `package`.
    include_summary:
        If False (default), return exactly the original `(order, levels)`
        contract, unchanged. If True, additionally compute and return
        `operation_summary` as a third tuple element.

    Returns
    -------
    (order, levels)
        when `include_summary` is False (original, unchanged contract).
    (order, levels, operation_summary)
        when `include_summary` is True.

        order   -- deterministic build order, or [] if a cycle exists.
        levels  -- longest chain length + 1, or -1 if a cycle exists.
        operation_summary -- dict described above (only when requested).
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

    # Deterministic min-heap frontier: seeded via heapify, updated only via
    # heappush/heappop. Guarantees lexicographically-smallest-first order
    # among simultaneously-ready packages, regardless of input ordering.
    ready_heap: List[T] = [p for p in package_list if indegree[p] == 0]
    heapq.heapify(ready_heap)

    order: List[T] = []

    # --- operation counters (only meaningful when include_summary=True,
    # but computed unconditionally since they add negligible cost and
    # must reflect the exact same deterministic run that produced order) ---
    heap_pops = 0
    heap_pushes = len(ready_heap)  # initial seeding counts as pushes
    edge_relaxations = 0
    depth_updates = 0

    while ready_heap:
        node = heapq.heappop(ready_heap)
        heap_pops += 1
        order.append(node)

        for nxt in graph[node]:
            indegree[nxt] -= 1
            edge_relaxations += 1
            if depth[node] + 1 > depth[nxt]:
                depth[nxt] = depth[node] + 1
                depth_updates += 1
            if indegree[nxt] == 0:
                heapq.heappush(ready_heap, nxt)
                heap_pushes += 1

    cycle_detected = len(order) != len(package_list)

    if cycle_detected:
        result_order: List[T] = []
        result_levels = -1
    else:
        result_order = order
        result_levels = (max(depth.values()) + 1) if package_list else 0

    if not include_summary:
        # Original, unchanged contract.
        return result_order, result_levels

    operation_summary: OperationSummary = {
        "heap_pops": heap_pops,
        "heap_pushes": heap_pushes,
        "edge_relaxations": edge_relaxations,
        "depth_updates": depth_updates,
        "cycle_detected": cycle_detected,
    }
    return result_order, result_levels, operation_summary


def _demo() -> None:
    print("1) Default call (include_summary=False) -- original contract unchanged")
    packages = ["a", "b", "c", "d", "e", "f"]
    prerequisites = [
        ("b", "a"),
        ("c", "a"),
        ("d", "b"),
        ("d", "c"),
        ("e", "d"),
        ("f", "a"),
    ]
    result = build_order(packages, prerequisites)
    print("  result:", result)
    assert result == (["a", "b", "c", "f", "d", "e"], 4)
    assert len(result) == 2  # exactly the original 2-tuple, nothing more

    print("\n2) Same input, include_summary=True -- additive third field")
    result_with_summary = build_order(packages, prerequisites, include_summary=True)
    order, levels, summary = result_with_summary
    print("  order  :", order)
    print("  levels :", levels)
    print("  summary:", summary)
    assert order == ["a", "b", "c", "f", "d", "e"]
    assert levels == 4
    assert summary == {
        "heap_pops": 6,
        "heap_pushes": 6,
        "edge_relaxations": 6,
        "depth_updates": 6,
        "cycle_detected": False,
    }

    print("\n3) Determinism: repeated calls with summary produce identical output")
    result_repeat = build_order(packages, prerequisites, include_summary=True)
    assert result_repeat == result_with_summary

    print("\n4) Cycle case, both modes")
    cyc_packages = ["p", "q", "r"]
    cyc_prereqs = [("p", "q"), ("q", "r"), ("r", "p")]

    plain = build_order(cyc_packages, cyc_prereqs)
    print("  plain  :", plain)
    assert plain == ([], -1)

    with_summary = build_order(cyc_packages, cyc_prereqs, include_summary=True)
    print("  summary:", with_summary)
    assert with_summary[0] == [] and with_summary[1] == -1
    assert with_summary[2]["cycle_detected"] is True

    print("\nAll checks passed.")


if __name__ == "__main__":
    _demo()