import heapq
from typing import Dict, List, Tuple


def resolve_build_order(
    packages: List[str], dependencies: Dict[str, List[str]]
) -> Tuple[List[str], int]:
    """
    Computes a deterministic valid build order and the maximum dependency levels.

    :param packages: List of all unique package names.
    :param dependencies: Dict where key is a package and value is a list of its prerequisites.
    :return: A tuple of (deterministic_build_order, max_dependency_levels).
             Returns ([], -1) if a cyclic dependency exists.
    """
    if not packages:
        return [], 0

    # Initialize in-degrees, graph edges, and level counters
    in_degree = {pkg: 0 for pkg in packages}
    graph = {pkg: [] for pkg in packages}
    level = {pkg: 1 for pkg in packages}

    # Build adjacency list: prerequisite -> dependent package
    for pkg, prereqs in dependencies.items():
        if pkg not in in_degree:
            continue
        for req in prereqs:
            if req in graph:
                graph[req].append(pkg)
                in_degree[pkg] += 1

    # Min-heap guarantees deterministic lexicographical order among zero in-degree nodes
    min_heap = [pkg for pkg, deg in in_degree.items() if deg == 0]
    heapq.heapify(min_heap)

    build_order = []

    while min_heap:
        current = heapq.heappop(min_heap)
        build_order.append(current)

        for neighbor in graph[current]:
            # Track the longest prerequisite depth to neighbor
            level[neighbor] = max(level[neighbor], level[current] + 1)
            in_degree[neighbor] -= 1

            if in_degree[neighbor] == 0:
                heapq.heappush(min_heap, neighbor)

    # Cycle check
    if len(build_order) != len(packages):
        return [], -1

    max_levels = max(level.values()) if packages else 0
    return build_order, max_levels


if __name__ == "__main__":
    # Test Case demonstrating the defect fix:
    # A (lvl 1) -> B (lvl 2) -> C (lvl 3)
    # Both B and C are prerequisites of D.
    # D must have level max(lvl(B)+1, lvl(C)+1) = max(3, 4) = 4.
    pkgs = ["A", "B", "C", "D"]
    deps = {"A": [], "B": ["A"], "C": ["B"], "D": ["B", "C"]}

    order, levels = resolve_build_order(pkgs, deps)
    print("Build Order:", order)  # Expected: ['A', 'B', 'C', 'D']
    print("Levels:", levels)  # Expected: 4