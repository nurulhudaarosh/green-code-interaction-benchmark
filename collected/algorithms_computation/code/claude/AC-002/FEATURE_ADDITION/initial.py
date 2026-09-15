"""
Deterministic package build-order resolver.

Given a list of packages and prerequisite pairs (a, b) meaning
"package a depends on package b" (b must be built before a),
compute:
  1. A deterministic valid build order (topological sort).
  2. The number of dependency levels (longest prerequisite chain).

If a cycle exists, returns ([], -1).

Standard library only. No randomness, no network, no external services.
"""

import heapq
from collections import defaultdict
from typing import List, Tuple, Dict, Set


def build_order(packages: List[str], prerequisites: List[Tuple[str, str]]) -> Tuple[List[str], int]:
    """
    Args:
        packages: list of all package names (may include isolated packages).
        prerequisites: list of (package, prerequisite) tuples meaning
                        `package` depends on `prerequisite`.

    Returns:
        (order, levels):
            order  - deterministic list of packages in valid build order,
                     or [] if a cycle is detected.
            levels - number of dependency levels (max chain length),
                     or -1 if a cycle is detected.
    """
    # Normalize: ensure every referenced package is known.
    all_packages: Set[str] = set(packages)
    for a, b in prerequisites:
        all_packages.add(a)
        all_packages.add(b)

    graph: Dict[str, Set[str]] = defaultdict(set)   # prereq -> dependents
    in_degree: Dict[str, int] = {p: 0 for p in all_packages}

    for pkg, prereq in prerequisites:
        if pkg not in graph[prereq]:
            graph[prereq].add(pkg)
            in_degree[pkg] += 1

    # depth[p] = 1 + max(depth of all prerequisites of p); 1 if no prerequisites.
    depth: Dict[str, int] = {p: 1 for p in all_packages}

    # Min-heap keyed on package name for deterministic tie-breaking.
    heap = [p for p, deg in in_degree.items() if deg == 0]
    heapq.heapify(heap)

    order: List[str] = []

    while heap:
        current = heapq.heappop(heap)
        order.append(current)

        # Process dependents in sorted order for determinism when
        # multiple become available at once (heap already guarantees
        # final pop order, but we push deterministically too).
        for dependent in sorted(graph[current]):
            depth[dependent] = max(depth[dependent], depth[current] + 1)
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                heapq.heappush(heap, dependent)

    if len(order) != len(all_packages):
        # Not all packages could be ordered -> cycle exists.
        return [], -1

    levels = max(depth.values()) if order else 0
    return order, levels


def _demo() -> None:
    packages = ["a", "b", "c", "d", "e"]
    # a depends on b and c; b depends on d; c depends on d; e has no deps.
    prerequisites = [
        ("a", "b"),
        ("a", "c"),
        ("b", "d"),
        ("c", "d"),
    ]
    order, levels = build_order(packages, prerequisites)
    print("Build order:", order)
    print("Levels:", levels)

    # Cycle example: x -> y -> z -> x
    cyclic_packages = ["x", "y", "z"]
    cyclic_prereqs = [("x", "y"), ("y", "z"), ("z", "x")]
    order2, levels2 = build_order(cyclic_packages, cyclic_prereqs)
    print("Cyclic build order:", order2)
    print("Cyclic levels:", levels2)


if __name__ == "__main__":
    _demo()