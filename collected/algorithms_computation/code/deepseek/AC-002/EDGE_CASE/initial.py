"""
Package Build Order with Dependency Levels

Problem:
Given a list of packages and their prerequisite dependencies, produce:
1. A deterministic valid build order (topological sort)
2. The number of dependency levels (longest chain of dependencies)

If a cycle exists, return an empty order and -1 levels.

Constraints:
- Packages are identified by strings
- Dependencies are given as a list of (package, prerequisite) pairs
- Each package can have multiple prerequisites
- A package can only be built after all its prerequisites are built
- The build order must be deterministic (use min-heap for alphabetical ordering)
- Dependency levels: the depth of the longest prerequisite chain + 1

Algorithm:
1. Build adjacency list and indegree map from the dependency pairs
2. Use Kahn's algorithm with a min-heap (priority queue) for deterministic ordering
3. Track the level (depth) of each package as max(level[prereq]) + 1
4. If all packages are processed, return order and max level
5. If not all packages are processed, a cycle exists -> return [], -1
"""

import heapq
from collections import defaultdict, deque
from typing import List, Tuple, Dict, Set


def find_build_order(packages: List[str], dependencies: List[Tuple[str, str]]) -> Tuple[List[str], int]:
    """
    Find a valid build order and the number of dependency levels.
    
    Args:
        packages: List of all package names
        dependencies: List of (package, prerequisite) tuples
        
    Returns:
        Tuple of (build_order, levels)
        - build_order: list of packages in build order, or [] if cycle
        - levels: number of dependency levels, or -1 if cycle
    """
    # Edge case: no packages
    if not packages:
        return [], 0
    
    # Build graph: package -> list of prerequisites
    graph: Dict[str, List[str]] = {pkg: [] for pkg in packages}
    indegree: Dict[str, int] = {pkg: 0 for pkg in packages}
    
    # Track all packages that appear in dependencies (to handle missing packages)
    all_pkgs_in_deps: Set[str] = set()
    for pkg, prereq in dependencies:
        all_pkgs_in_deps.add(pkg)
        all_pkgs_in_deps.add(prereq)
        graph[pkg].append(prereq)
        indegree[pkg] += 1
    
    # Ensure all packages from dependencies are in the package list
    # If a package appears only as a dependency but not in the main list,
    # we add it as an independent package (no dependencies)
    for pkg in all_pkgs_in_deps:
        if pkg not in graph:
            graph[pkg] = []
            indegree[pkg] = 0
            packages.append(pkg)  # Add to package list for completeness
    
    # Initialize min-heap with packages that have indegree 0
    heap = [pkg for pkg, deg in indegree.items() if deg == 0]
    heapq.heapify(heap)
    
    # Track levels (depth) for each package
    levels: Dict[str, int] = {pkg: 1 for pkg in packages}  # Default level 1
    max_level = 0
    build_order: List[str] = []
    
    # Kahn's algorithm with level tracking
    while heap:
        # Pop the smallest package alphabetically (deterministic)
        current = heapq.heappop(heap)
        build_order.append(current)
        
        # Update level for current package
        # The level is already set when we pushed it, but we ensure it's correct
        # For packages with no prerequisites, level is 1
        
        # Process all packages that depend on current (reverse dependencies)
        # We need to find packages where current is a prerequisite
        for pkg in packages:
            if current in graph[pkg]:
                # current is a prerequisite of pkg
                indegree[pkg] -= 1
                # Update level: level[pkg] = max(level[pkg], level[current] + 1)
                levels[pkg] = max(levels[pkg], levels[current] + 1)
                if indegree[pkg] == 0:
                    heapq.heappush(heap, pkg)
    
    # Check if all packages were processed (no cycle)
    if len(build_order) != len(graph):
        return [], -1
    
    # Calculate max level
    max_level = max(levels.values()) if levels else 0
    
    return build_order, max_level


def solve_build_order(packages: List[str], dependencies: List[Tuple[str, str]]) -> Tuple[List[str], int]:
    """
    Wrapper function that handles edge cases and provides the required output format.
    
    Args:
        packages: List of all package names
        dependencies: List of (package, prerequisite) tuples
        
    Returns:
        Tuple of (build_order, levels)
    """
    # Handle empty package list
    if not packages:
        return [], 0
    
    # Handle case with no dependencies
    if not dependencies:
        # All packages are independent, build in alphabetical order
        return sorted(packages), 1
    
    # Find build order
    order, levels = find_build_order(packages, dependencies)
    
    return order, levels


# ==================== TEST CASES ====================
if __name__ == "__main__":
    # Test Case 1: Simple linear dependency
    packages1 = ["A", "B", "C"]
    deps1 = [("B", "A"), ("C", "B")]
    order1, levels1 = solve_build_order(packages1, deps1)
    print(f"Test 1: {order1}, Levels: {levels1}")
    # Expected: ['A', 'B', 'C'], Levels: 3
    
    # Test Case 2: Multiple dependencies
    packages2 = ["A", "B", "C", "D"]
    deps2 = [("C", "A"), ("C", "B"), ("D", "C")]
    order2, levels2 = solve_build_order(packages2, deps2)
    print(f"Test 2: {order2}, Levels: {levels2}")
    # Expected: ['A', 'B', 'C', 'D'], Levels: 3 (A and B are level 1, C is level 2, D is level 3)
    
    # Test Case 3: Cycle
    packages3 = ["A", "B", "C"]
    deps3 = [("B", "A"), ("C", "B"), ("A", "C")]
    order3, levels3 = solve_build_order(packages3, deps3)
    print(f"Test 3: {order3}, Levels: {levels3}")
    # Expected: [], Levels: -1
    
    # Test Case 4: Independent packages
    packages4 = ["C", "A", "B"]
    deps4 = []
    order4, levels4 = solve_build_order(packages4, deps4)
    print(f"Test 4: {order4}, Levels: {levels4}")
    # Expected: ['A', 'B', 'C'], Levels: 1 (sorted alphabetically)
    
    # Test Case 5: Package with multiple prerequisites
    packages5 = ["A", "B", "C", "D"]
    deps5 = [("C", "A"), ("C", "B"), ("D", "A"), ("D", "B")]
    order5, levels5 = solve_build_order(packages5, deps5)
    print(f"Test 5: {order5}, Levels: {levels5}")
    # Expected: ['A', 'B', 'C', 'D'], Levels: 2 (A and B are level 1, C and D are level 2)
    
    # Test Case 6: Package not in initial list but appears as dependency
    packages6 = ["A", "C"]
    deps6 = [("C", "B"), ("B", "A")]
    order6, levels6 = solve_build_order(packages6, deps6)
    print(f"Test 6: {order6}, Levels: {levels6}")
    # Expected: ['A', 'B', 'C'], Levels: 3
    
    # Test Case 7: Complex with alphabetical ordering
    packages7 = ["Z", "A", "M", "N"]
    deps7 = [("Z", "A"), ("Z", "M"), ("N", "M")]
    order7, levels7 = solve_build_order(packages7, deps7)
    print(f"Test 7: {order7}, Levels: {levels7}")
    # Expected: ['A', 'M', 'N', 'Z'] or similar deterministic order
    # With min-heap: A (level 1), M (level 1), N (level 2), Z (level 2)
    
    # Test Case 8: Empty packages
    packages8 = []
    deps8 = []
    order8, levels8 = solve_build_order(packages8, deps8)
    print(f"Test 8: {order8}, Levels: {levels8}")
    # Expected: [], Levels: 0