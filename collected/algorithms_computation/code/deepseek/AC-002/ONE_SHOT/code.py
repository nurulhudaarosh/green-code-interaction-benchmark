"""
Package Build Order with Dependency Levels

Given:
- packages: List of package names (strings)
- dependencies: List of (package, prerequisite) tuples

Find:
- A deterministic valid build order (lexicographically smallest among valid orders)
- Number of dependency levels (longest chain length)

If a cycle exists:
- Return empty order []
- Return -1 for levels

Algorithm:
1. Build adjacency graph and in-degree counts
2. Use Kahn's topological sorting with a min-heap for deterministic order
3. Track depth levels using DP: level[node] = 1 + max(level[prereq])
4. Detect cycles by counting processed nodes vs total packages
"""

from collections import defaultdict, deque
import heapq
from typing import List, Tuple, Dict, Set


def build_order(
    packages: List[str], dependencies: List[Tuple[str, str]]
) -> Tuple[List[str], int]:
    """
    Returns:
        - order: List of package names in build order
        - levels: Number of dependency levels (longest chain)
    """
    # Build graph: package -> list of dependents (packages that depend on it)
    graph: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {pkg: 0 for pkg in packages}

    # Also track reverse graph for level calculation (prereq -> dependent)
    reverse_graph: Dict[str, List[str]] = defaultdict(list)

    for pkg, prereq in dependencies:
        if pkg not in in_degree or prereq not in in_degree:
            # Skip invalid dependencies (should not happen with valid input)
            continue
        graph[prereq].append(pkg)
        reverse_graph[prereq].append(pkg)  # prereq -> dependent
        in_degree[pkg] += 1

    # Min-heap for deterministic ordering (lexicographically smallest)
    heap = [pkg for pkg, deg in in_degree.items() if deg == 0]
    heapq.heapify(heap)

    order = []
    # Track depth (levels) for each package
    # depth[pkg] = 1 + max(depth[prereq] for prereq in dependencies where pkg depends on prereq)
    depth: Dict[str, int] = {pkg: 1 for pkg in packages}
    # We'll compute depth when we pop a package: it gets its final depth then

    # For cycle detection: if we process fewer than len(packages) nodes, there's a cycle
    processed = 0

    while heap:
        current = heapq.heappop(heap)
        order.append(current)
        processed += 1

        # Update depth for dependents
        for dependent in graph[current]:
            # The dependent's depth is at least depth[current] + 1
            if depth[dependent] < depth[current] + 1:
                depth[dependent] = depth[current] + 1

            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                heapq.heappush(heap, dependent)

    # Check for cycle
    if processed != len(packages):
        return [], -1

    # Compute max depth
    max_levels = max(depth.values()) if depth else 0
    return order, max_levels


def main():
    """Test the implementation with various cases."""
    print("=== Test Case 1: Simple chain ===")
    packages1 = ["A", "B", "C"]
    deps1 = [("B", "A"), ("C", "B")]
    order1, levels1 = build_order(packages1, deps1)
    print(f"Order: {order1}, Levels: {levels1}")
    # Expected: ['A', 'B', 'C'], 3

    print("\n=== Test Case 2: Diamond dependencies ===")
    packages2 = ["A", "B", "C", "D"]
    deps2 = [("B", "A"), ("C", "A"), ("D", "B"), ("D", "C")]
    order2, levels2 = build_order(packages2, deps2)
    print(f"Order: {order2}, Levels: {levels2}")
    # Expected: ['A', 'B', 'C', 'D'] or ['A', 'C', 'B', 'D'], but min-heap gives ['A', 'B', 'C', 'D']

    print("\n=== Test Case 3: Independent packages ===")
    packages3 = ["X", "Y", "Z"]
    deps3 = []
    order3, levels3 = build_order(packages3, deps3)
    print(f"Order: {order3}, Levels: {levels3}")
    # Expected: ['X', 'Y', 'Z'], 1

    print("\n=== Test Case 4: Cycle detected ===")
    packages4 = ["A", "B", "C"]
    deps4 = [("B", "A"), ("C", "B"), ("A", "C")]
    order4, levels4 = build_order(packages4, deps4)
    print(f"Order: {order4}, Levels: {levels4}")
    # Expected: [], -1

    print("\n=== Test Case 5: Lexicographic ordering ===")
    packages5 = ["Z", "Y", "X", "W"]
    deps5 = [("Y", "W"), ("Z", "W"), ("X", "W")]
    order5, levels5 = build_order(packages5, deps5)
    print(f"Order: {order5}, Levels: {levels5}")
    # Expected: ['W', 'X', 'Y', 'Z'] (lexicographically smallest among dependents)

    print("\n=== Test Case 6: Complex with multiple levels ===")
    packages6 = ["A", "B", "C", "D", "E", "F"]
    deps6 = [
        ("B", "A"),
        ("C", "A"),
        ("D", "B"),
        ("E", "C"),
        ("F", "D"),
        ("F", "E"),
    ]
    order6, levels6 = build_order(packages6, deps6)
    print(f"Order: {order6}, Levels: {levels6}")
    # Expected: ['A', 'B', 'C', 'D', 'E', 'F'], 4

    print("\n=== Test Case 7: Empty packages ===")
    packages7 = []
    deps7 = []
    order7, levels7 = build_order(packages7, deps7)
    print(f"Order: {order7}, Levels: {levels7}")
    # Expected: [], 0


if __name__ == "__main__":
    main()