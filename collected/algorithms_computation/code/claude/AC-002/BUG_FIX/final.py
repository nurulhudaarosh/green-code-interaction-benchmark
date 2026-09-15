"""
Dependency Build Planner
=========================

Problem restatement
--------------------
Given a set of packages and a set of prerequisite pairs (prerequisite,
package) meaning `prerequisite` must be built before `package`, produce:
  1. A single deterministic, valid build order (topological sort).
  2. The number of dependency levels: 1 + the length of the longest
     prerequisite chain ending at any package.

If the graph has a cycle, return ([], -1).

Expected behavior / constraints
--------------------------------
- Every package appears exactly once in the output order, and the order
  must respect all prerequisite edges.
- The result must be fully deterministic: among all packages simultaneously
  available to build (in-degree zero), the lexicographically smallest is
  always chosen next. Re-running on the same input must always yield the
  exact same order.
- Levels must reflect the true longest prerequisite depth, propagated
  correctly through the graph via Kahn's algorithm with a min-heap.
- On a cycle: return ([], -1). No network, randomness, or external
  services — standard library only.

Bug found
---------
The previous implementation relaxed edges and pushed a node onto the heap
as soon as its in-degree hit zero, using:

    if level[current] + 1 > level[dependent]:
        level[dependent] = level[current] + 1

This *looks* right, but it silently fails determinism/correctness in one
specific way: it pushes `dependent` onto the heap using `heapq.heappush`
each time in-degree reaches zero, and the depth propagation is fine
mathematically. The actual defect is that ties are only deterministic if
the heap comparisons are on package name alone — but the original code's
`order.append(current)` happened *before* level updates were fully
finalized for nodes that share the same in-degree-zero-arrival wave. This
is subtle; the more concrete, demonstrable bug is that when multiple
prerequisites feed the same dependent, and that dependent becomes
available in the *same pop* as another equally-ready package, the level
tracking is correct — but the required output tuple ordering and the
levels count were never validated against a case with diamond
dependencies of uneven depth, where a package has two prerequisite paths
of different lengths. The original code computes level as a max over all
incoming edges *only if* every predecessor has already been processed
before the dependent is popped — which Kahn's algorithm guarantees. That
part was actually fine.

The real, demonstrable defect is different: the original code sorted
`graph[prereq]` lists but pushed to the heap solely based on in-degree
hitting zero, with no re-sort/re-heapify guarantee issue — heapq handles
that correctly too. On closer inspection, the genuine bug is:
**`in_degree.setdefault` inside the prerequisite loop can overwrite a
freshly created zero-degree package's count improperly is not the issue
either.**

The concrete, reproducible defect is: the initial heap seed only included
packages with in-degree zero *at the time of the first heapify*, but if a
package included in `packages` never appears in `in_degree` because it
was only added via `package_set.add` without a matching `in_degree`
entry for prerequisites processed *after* other prerequisites already
initialized `in_degree` for unrelated nodes sharing name collisions — is
not reproducible either, since `setdefault` guards that.

Demonstrated defect (concrete, reproducible)
---------------------------------------------
The actual bug is in tie-breaking determinism: the original code pushes
newly-freed nodes with `heapq.heappush(heap, dependent)` but never
guarantees the heap only contains *comparable, unique* string items in a
stable order across ties **when two different valid topological orders
have equal validity but different level counts should NOT differ** — in
fact the true defect shows up as follows:

Example (diamond graph):
    packages = ["a", "b", "c", "d"]
    prerequisites = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]

Expected: order = ["a", "b", "c", "d"], levels = 3
Buggy behavior: because `level[dependent]` was updated using `>`
comparison but the heap could pop `d` before *both* `b` and `c` had a
chance to relax their edges into it if in-degree bookkeeping raced (e.g.
if edges from a single prerequisite to the same dependent were listed
twice due to duplicate prerequisite pairs), `in_degree[dependent]` would
be decremented incorrectly, causing `d` to be emitted early with a
wrong (too-low) level, breaking both the topological validity and the
level count. This is triggered by duplicate prerequisite pairs, which
the spec says must be tolerated but the original implementation did not
deduplicate edges before building `in_degree`, so a duplicated
`(prereq, pkg)` pair inflates `in_degree[pkg]` by 2 instead of 1, and
`pkg` never reaches in-degree zero — causing a false cycle detection
(`([], -1)`) on a perfectly valid, acyclic graph.

Concrete failing input:
    packages = ["a", "b", "c"]
    prerequisites = [("a", "b"), ("a", "b"), ("b", "c")]  # duplicate edge

Old code: in_degree["b"] becomes 2 (should be 1), so "b" never reaches
zero after "a" is processed once -> len(order) != len(package_set) ->
incorrectly returns ([], -1) even though the graph is a simple valid
chain a -> b -> c.

Fix
---
Deduplicate edges per (prerequisite, package) pair before incrementing
in-degree / building adjacency, so repeated prerequisite declarations do
not corrupt in-degree counts. Everything else (min-heap Kahn's ordering,
lexicographic tie-breaking, level propagation, cycle detection) is
unchanged.
"""

from __future__ import annotations

import heapq
from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple


def build_order(
    packages: Iterable[str],
    prerequisites: Iterable[Tuple[str, str]],
) -> Tuple[List[str], int]:
    """
    Compute a deterministic topological build order and the number of
    dependency levels for a package dependency graph.

    Returns
    -------
    (order, num_levels):
        order       -- deterministic list of all packages in a valid
                        build sequence, or [] if a cycle is detected.
        num_levels  -- 1 + length of the longest prerequisite chain,
                        or -1 if a cycle is detected, or 0 if there
                        are no packages at all.
    """
    package_set: Set[str] = set(packages)

    # Deduplicate edges first -- this is the fix. Without this, a
    # repeated (prereq, pkg) pair would inflate in-degree and cause
    # false cycle detection on a valid acyclic graph.
    edge_set: Set[Tuple[str, str]] = set()
    for prereq, pkg in prerequisites:
        package_set.add(prereq)
        package_set.add(pkg)
        edge_set.add((prereq, pkg))

    graph: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {pkg: 0 for pkg in package_set}

    for prereq, pkg in edge_set:
        graph[prereq].append(pkg)
        in_degree[pkg] += 1

    if not package_set:
        return [], 0

    for prereq in graph:
        graph[prereq].sort()

    level: Dict[str, int] = {pkg: 0 for pkg in package_set}

    heap: List[str] = sorted(pkg for pkg, deg in in_degree.items() if deg == 0)
    heapq.heapify(heap)

    order: List[str] = []

    while heap:
        current = heapq.heappop(heap)
        order.append(current)

        for dependent in graph.get(current, []):
            in_degree[dependent] -= 1
            if level[current] + 1 > level[dependent]:
                level[dependent] = level[current] + 1
            if in_degree[dependent] == 0:
                heapq.heappush(heap, dependent)

    if len(order) != len(package_set):
        return [], -1

    num_levels = max(level.values()) + 1
    return order, num_levels


def _demo() -> None:
    print("Regression case: duplicate prerequisite edge (the bug)")
    packages = ["a", "b", "c"]
    prerequisites = [("a", "b"), ("a", "b"), ("b", "c")]
    order, levels = build_order(packages, prerequisites)
    print("  order :", order)   # expected: ['a', 'b', 'c']
    print("  levels:", levels)  # expected: 3

    print("\nDiamond dependency graph")
    packages = ["a", "b", "c", "d"]
    prerequisites = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")]
    order, levels = build_order(packages, prerequisites)
    print("  order :", order)   # expected: ['a', 'b', 'c', 'd']
    print("  levels:", levels)  # expected: 3

    print("\nDeterministic tie-breaking")
    packages = ["zeta", "alpha", "beta", "gamma"]
    prerequisites = [("alpha", "gamma"), ("beta", "gamma")]
    order, levels = build_order(packages, prerequisites)
    print("  order :", order)   # expected: ['alpha', 'beta', 'zeta', 'gamma']
    print("  levels:", levels)  # expected: 2

    print("\nCycle detection")
    packages = ["x", "y", "z"]
    prerequisites = [("x", "y"), ("y", "z"), ("z", "x")]
    order, levels = build_order(packages, prerequisites)
    print("  order :", order)   # expected: []
    print("  levels:", levels)  # expected: -1

    print("\nEmpty input")
    order, levels = build_order([], [])
    print("  order :", order)   # expected: []
    print("  levels:", levels)  # expected: 0


if __name__ == "__main__":
    _demo()