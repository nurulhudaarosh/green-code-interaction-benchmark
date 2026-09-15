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


def test_find_build_order() -> None:
    """
    Comprehensive test suite for find_build_order function.
    Tests include edge cases, repeated values, and deterministic tie handling.
    """
    print("=" * 60)
    print("DEPENDENCY BUILD PLANNER - TEST SUITE")
    print("=" * 60)
    
    # Test 1: Simple linear dependency
    packages1 = ["A", "B", "C", "D"]
    deps1 = [("B", "A"), ("C", "B"), ("D", "C")]
    order1, levels1 = find_build_order(packages1, deps1)
    print(f"\nTest 1 - Linear:")
    print(f"  Dependencies: {deps1}")
    print(f"  Order: {order1}")
    print(f"  Levels: {levels1}")
    assert order1 == ['A', 'B', 'C', 'D'], f"Expected ['A','B','C','D'], got {order1}"
    assert levels1 == 4, f"Expected 4, got {levels1}"

    # Test 2: Multiple dependencies (critical bug fix case)
    packages2 = ["A", "B", "C", "D"]
    deps2 = [("C", "A"), ("C", "B"), ("D", "C")]
    order2, levels2 = find_build_order(packages2, deps2)
    print(f"\nTest 2 - Multiple Dependencies:")
    print(f"  Dependencies: {deps2}")
    print(f"  Order: {order2}")
    print(f"  Levels: {levels2}")
    assert order2 == ['A', 'B', 'C', 'D'], f"Expected ['A','B','C','D'], got {order2}"
    assert levels2 == 3, f"Expected 3, got {levels2}"

    # Test 3: Complex with different depths
    packages3 = ["A", "B", "C", "D", "E"]
    deps3 = [("D", "A"), ("D", "B"), ("E", "D"), ("E", "C")]
    order3, levels3 = find_build_order(packages3, deps3)
    print(f"\nTest 3 - Complex:")
    print(f"  Dependencies: {deps3}")
    print(f"  Order: {order3}")
    print(f"  Levels: {levels3}")
    assert order3 == ['A', 'B', 'C', 'D', 'E'], f"Expected ['A','B','C','D','E'], got {order3}"
    assert levels3 == 3, f"Expected 3, got {levels3}"

    # Test 4: Deep chain with branches
    packages4 = ["A", "B", "C", "D", "E", "F"]
    deps4 = [("B", "A"), ("C", "A"), ("D", "B"), ("E", "C"), ("F", "D"), ("F", "E")]
    order4, levels4 = find_build_order(packages4, deps4)
    print(f"\nTest 4 - Branched:")
    print(f"  Dependencies: {deps4}")
    print(f"  Order: {order4}")
    print(f"  Levels: {levels4}")
    assert order4 == ['A', 'B', 'C', 'D', 'E', 'F'], f"Expected ['A','B','C','D','E','F'], got {order4}"
    assert levels4 == 4, f"Expected 4, got {levels4}"

    # Test 5: Deterministic tie handling - packages with no dependencies
    packages5 = ["Z", "Y", "X", "W"]
    deps5 = []
    order5, levels5 = find_build_order(packages5, deps5)
    print(f"\nTest 5 - No Dependencies (Tie Handling):")
    print(f"  Dependencies: {deps5}")
    print(f"  Order: {order5}")
    print(f"  Levels: {levels5}")
    assert order5 == ['W', 'X', 'Y', 'Z'], f"Expected ['W','X','Y','Z'] (alphabetical), got {order5}"
    assert levels5 == 1, f"Expected 1, got {levels5}"

    # Test 6: Deterministic tie handling - multiple independent packages after prerequisites
    packages6 = ["Z", "Y", "X", "W", "V"]
    deps6 = [("Z", "W"), ("Y", "W"), ("X", "W")]
    order6, levels6 = find_build_order(packages6, deps6)
    print(f"\nTest 6 - Multiple Dependents (Tie Handling):")
    print(f"  Dependencies: {deps6}")
    print(f"  Order: {order6}")
    print(f"  Levels: {levels6}")
    # W at level 0, then V (independent) at level 0, then X,Y,Z at level 1
    # V should come after W since it's already in heap
    assert order6 == ['V', 'W', 'X', 'Y', 'Z'] or order6 == ['W', 'V', 'X', 'Y', 'Z'], \
        f"Expected ['V','W','X','Y','Z'] or ['W','V','X','Y','Z'], got {order6}"
    assert levels6 == 2, f"Expected 2, got {levels6}"

    # Test 7: Cycle detection
    packages7 = ["A", "B", "C"]
    deps7 = [("A", "B"), ("B", "C"), ("C", "A")]
    order7, levels7 = find_build_order(packages7, deps7)
    print(f"\nTest 7 - Cycle Detection:")
    print(f"  Dependencies: {deps7}")
    print(f"  Order: {order7}")
    print(f"  Levels: {levels7}")
    assert order7 == [], f"Expected [], got {order7}"
    assert levels7 == -1, f"Expected -1, got {levels7}"

    # Test 8: Empty packages
    order8, levels8 = find_build_order([], [])
    print(f"\nTest 8 - Empty Packages:")
    print(f"  Dependencies: []")
    print(f"  Order: {order8}")
    print(f"  Levels: {levels8}")
    assert order8 == [], f"Expected [], got {order8}"
    assert levels8 == 0, f"Expected 0, got {levels8}"

    # Test 9: Invalid dependency
    packages9 = ["A", "B"]
    deps9 = [("A", "C")]  # C doesn't exist
    order9, levels9 = find_build_order(packages9, deps9)
    print(f"\nTest 9 - Invalid Dependency:")
    print(f"  Dependencies: {deps9}")
    print(f"  Order: {order9}")
    print(f"  Levels: {levels9}")
    assert order9 == [], f"Expected [], got {order9}"
    assert levels9 == -1, f"Expected -1, got {levels9}"

    # Test 10: Repeated dependencies (should handle gracefully)
    packages10 = ["A", "B", "C"]
    deps10 = [("B", "A"), ("B", "A"), ("C", "B"), ("C", "B")]
    order10, levels10 = find_build_order(packages10, deps10)
    print(f"\nTest 10 - Repeated Dependencies:")
    print(f"  Dependencies: {deps10}")
    print(f"  Order: {order10}")
    print(f"  Levels: {levels10}")
    assert order10 == ['A', 'B', 'C'], f"Expected ['A','B','C'], got {order10}"
    assert levels10 == 3, f"Expected 3, got {levels10}"

    # Test 11: Multiple prerequisites at different depths
    packages11 = ["A", "B", "C", "D", "E"]
    deps11 = [("D", "A"), ("D", "B"), ("D", "C"), ("E", "D")]
    order11, levels11 = find_build_order(packages11, deps11)
    print(f"\nTest 11 - Multiple Prerequisites at Same Depth:")
    print(f"  Dependencies: {deps11}")
    print(f"  Order: {order11}")
    print(f"  Levels: {levels11}")
    assert order11 == ['A', 'B', 'C', 'D', 'E'], f"Expected ['A','B','C','D','E'], got {order11}"
    assert levels11 == 3, f"Expected 3, got {levels11}"

    # Test 12: Complex with diamond dependency
    packages12 = ["A", "B", "C", "D", "E"]
    deps12 = [("C", "A"), ("D", "A"), ("E", "C"), ("E", "D")]
    order12, levels12 = find_build_order(packages12, deps12)
    print(f"\nTest 12 - Diamond Dependency:")
    print(f"  Dependencies: {deps12}")
    print(f"  Order: {order12}")
    print(f"  Levels: {levels12}")
    # A at level 0, B at level 0 (independent), C and D at level 1 (tie broken alphabetically), E at level 2
    assert order12 == ['A', 'B', 'C', 'D', 'E'] or order12 == ['B', 'A', 'C', 'D', 'E'], \
        f"Expected ['A','B','C','D','E'] or ['B','A','C','D','E'], got {order12}"
    assert levels12 == 3, f"Expected 3, got {levels12}"

    # Test 13: Packages with complex alphabetical ordering
    packages13 = ["Zebra", "Apple", "Banana", "Cherry", "Date"]
    deps13 = [("Banana", "Apple"), ("Cherry", "Apple"), ("Date", "Banana"), ("Date", "Cherry")]
    order13, levels13 = find_build_order(packages13, deps13)
    print(f"\nTest 13 - Complex Alphabetical:")
    print(f"  Dependencies: {deps13}")
    print(f"  Order: {order13}")
    print(f"  Levels: {levels13}")
    # Apple at level 0, Zebra at level 0 (alphabetically after? actually Apple, Zebra, then Banana/Cherry, then Date)
    # Let's verify the deterministic order
    assert order13[0] in ['Apple', 'Zebra'], f"First element should be 'Apple' or 'Zebra', got {order13[0]}"
    assert levels13 == 3, f"Expected 3, got {levels13}"

    # Test 14: Single package with self-dependency (invalid)
    packages14 = ["A"]
    deps14 = [("A", "A")]
    order14, levels14 = find_build_order(packages14, deps14)
    print(f"\nTest 14 - Self-Dependency:")
    print(f"  Dependencies: {deps14}")
    print(f"  Order: {order14}")
    print(f"  Levels: {levels14}")
    assert order14 == [], f"Expected [], got {order14}"
    assert levels14 == -1, f"Expected -1, got {levels14}"

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


def main() -> None:
    """
    Run the test suite.
    """
    test_find_build_order()


if __name__ == "__main__":
    main()