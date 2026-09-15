#!/usr/bin/env python3
"""
Package Build Order with Dependency Levels

Given:
- packages: List of package names (strings)
- dependencies: List of (package, prerequisite) tuples

Return:
- build_order: List of package names in a valid build order
- levels: Number of dependency levels (longest chain length)

If a cycle exists, return ([], -1)

Algorithm:
1. Build adjacency list and indegree map
2. Use Kahn's topological sorting with a min-heap (deterministic order)
3. Track the longest prerequisite depth for each package
4. Number of levels = max depth + 1 (or 0 if no packages)
"""

from collections import defaultdict
import heapq
from typing import List, Tuple, Dict, Set


def find_build_order(packages: List[str], dependencies: List[Tuple[str, str]]) -> Tuple[List[str], int]:
    """
    Determine a valid build order and the number of dependency levels.

    Args:
        packages: List of all package names
        dependencies: List of (package, prerequisite) tuples

    Returns:
        (build_order, levels): Valid build order and number of levels
        Returns ([], -1) if a cycle is detected
    """
    if not packages:
        return [], 0

    # Build graph: package -> set of prerequisites
    graph: Dict[str, Set[str]] = defaultdict(set)
    # Reverse graph: prerequisite -> set of packages that depend on it
    reverse_graph: Dict[str, Set[str]] = defaultdict(set)
    indegree: Dict[str, int] = {pkg: 0 for pkg in packages}

    # Populate graphs
    for pkg, prereq in dependencies:
        # Validate both packages exist
        if pkg not in indegree or prereq not in indegree:
            # Invalid dependency, treat as cycle
            return [], -1

        if prereq not in graph[pkg]:
            graph[pkg].add(prereq)
            reverse_graph[prereq].add(pkg)
            indegree[pkg] += 1

    # Initialize min-heap with all packages that have indegree 0
    min_heap: List[str] = []
    for pkg, deg in indegree.items():
        if deg == 0:
            heapq.heappush(min_heap, pkg)

    build_order: List[str] = []
    # Track the longest prerequisite chain depth for each package
    # Initialize all packages with depth 0
    depth: Dict[str, int] = {pkg: 0 for pkg in packages}

    # Kahn's algorithm with min-heap for deterministic order
    while min_heap:
        pkg = heapq.heappop(min_heap)
        build_order.append(pkg)

        # Process all packages that depend on this one
        # Sort for deterministic processing (though depth calculation is now correct)
        for dependent in sorted(reverse_graph[pkg]):
            indegree[dependent] -= 1
            
            # CRITICAL FIX: The depth of a package should be the maximum depth
            # of all its prerequisites, not just the one being processed.
            # We update by checking if the current package's depth + 1 exceeds
            # the dependent's current depth.
            depth[dependent] = max(depth[dependent], depth[pkg] + 1)

            if indegree[dependent] == 0:
                heapq.heappush(min_heap, dependent)

    # Check for cycle: if not all packages were processed
    if len(build_order) != len(packages):
        return [], -1

    # Number of levels = max depth + 1 (if there are packages)
    max_depth = max(depth.values()) if depth else 0
    levels = max_depth + 1

    return build_order, levels


def main() -> None:
    """
    Example usage and test cases.
    """
    # Test case 1: Simple linear dependency
    packages1 = ["A", "B", "C", "D"]
    deps1 = [("B", "A"), ("C", "B"), ("D", "C")]
    order1, levels1 = find_build_order(packages1, deps1)
    print(f"Test 1 - Linear: {order1}, Levels: {levels1}")
    # Expected: ['A', 'B', 'C', 'D'], Levels: 4

    # Test case 2: Multiple dependencies (BUG FIX DEMONSTRATION)
    packages2 = ["A", "B", "C", "D"]
    deps2 = [("C", "A"), ("C", "B"), ("D", "C")]
    order2, levels2 = find_build_order(packages2, deps2)
    print(f"Test 2 - Multiple deps: {order2}, Levels: {levels2}")
    # Expected: ['A', 'B', 'C', 'D'], Levels: 3
    # BEFORE FIX: Levels: 2 (incorrect)
    # AFTER FIX: Levels: 3 (correct)

    # Test case 3: More complex with different depths
    packages3 = ["A", "B", "C", "D", "E"]
    deps3 = [("D", "A"), ("D", "B"), ("E", "D"), ("E", "C")]
    order3, levels3 = find_build_order(packages3, deps3)
    print(f"Test 3 - Complex: {order3}, Levels: {levels3}")
    # Expected: ['A', 'B', 'C', 'D', 'E'], Levels: 3 (A/B/C at level 0, D at level 1, E at level 2)

    # Test case 4: Deep chain with branches
    packages4 = ["A", "B", "C", "D", "E", "F"]
    deps4 = [("B", "A"), ("C", "A"), ("D", "B"), ("E", "C"), ("F", "D"), ("F", "E")]
    order4, levels4 = find_build_order(packages4, deps4)
    print(f"Test 4 - Branched: {order4}, Levels: {levels4}")
    # Expected: ['A', 'B', 'C', 'D', 'E', 'F'], Levels: 4 (A=0, B/C=1, D/E=2, F=3)

    # Test case 5: Cycle detection
    packages5 = ["A", "B", "C"]
    deps5 = [("A", "B"), ("B", "C"), ("C", "A")]
    order5, levels5 = find_build_order(packages5, deps5)
    print(f"Test 5 - Cycle: {order5}, Levels: {levels5}")
    # Expected: [], -1

    # Test case 6: Empty packages
    order6, levels6 = find_build_order([], [])
    print(f"Test 6 - Empty: {order6}, Levels: {levels6}")
    # Expected: [], 0

    # Test case 7: Packages with no dependencies
    packages7 = ["X", "Y", "Z"]
    order7, levels7 = find_build_order(packages7, [])
    print(f"Test 7 - No deps: {order7}, Levels: {levels7}")
    # Expected: ['X', 'Y', 'Z'] (sorted by min-heap), Levels: 1

    # Test case 8: Invalid dependency
    packages8 = ["A", "B"]
    deps8 = [("A", "C")]  # C doesn't exist
    order8, levels8 = find_build_order(packages8, deps8)
    print(f"Test 8 - Invalid dep: {order8}, Levels: {levels8}")
    # Expected: [], -1

    # Test case 9: Verification of deterministic ordering with ties
    packages9 = ["Z", "Y", "X", "W"]
    deps9 = [("Z", "W"), ("Y", "W"), ("X", "W")]
    order9, levels9 = find_build_order(packages9, deps9)
    print(f"Test 9 - Deterministic ties: {order9}, Levels: {levels9}")
    # Expected: ['W', 'X', 'Y', 'Z'] (W first, then sorted X,Y,Z), Levels: 2


if __name__ == "__main__":
    main()