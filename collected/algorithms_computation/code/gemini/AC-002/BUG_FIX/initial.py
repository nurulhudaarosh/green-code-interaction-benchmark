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
    # Initialize in-degrees and adjacency list
    in_degree = {pkg: 0 for pkg in packages}
    graph = {pkg: [] for pkg in packages}
    depth = {pkg: 1 for pkg in packages}

    # Build graph: edge goes from prerequisite -> dependent package
    for pkg, prereqs in dependencies.items():
        if pkg not in in_degree:
            continue
        for req in prereqs:
            if req in graph:
                graph[req].append(pkg)
                in_degree[pkg] += 1

    # Min-heap ensures deterministic lexicographical ordering among zero in-degree nodes
    min_heap = [pkg for pkg, deg in in_degree.items() if deg == 0]
    heapq.heapify(min_heap)

    build_order = []
    max_level = 0 if not packages else 1

    while min_heap:
        current = heapq.heappop(min_heap)
        build_order.append(current)

        current_depth = depth[current]
        if current_depth > max_level:
            max_level = current_depth

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            # Propagate longest depth to child nodes
            depth[neighbor] = max(depth[neighbor], current_depth + 1)

            if in_degree[neighbor] == 0:
                heapq.heappush(min_heap, neighbor)

    # If build_order doesn't contain all packages, a cycle was detected
    if len(build_order) != len(packages):
        return [], -1

    return build_order, max_level


if __name__ == "__main__":
    # Test Case 1: Valid DAG with multiple levels & tie-breaking
    pkgs1 = ["A", "B", "C", "D", "E"]
    deps1 = {
        "A": [],
        "B": ["A"],
        "C": ["A"],
        "D": ["B", "C"],
        "E": ["D"],
    }
    order1, levels1 = resolve_build_order(pkgs1, deps1)
    print("Test 1 (Valid DAG):")
    print("Build Order:", order1)  # Expected: ['A', 'B', 'C', 'D', 'E']
    print("Levels:", levels1)  # Expected: 4

    print("-" * 40)

    # Test Case 2: Cyclic Dependencies
    pkgs2 = ["A", "B", "C"]
    deps2 = {"A": ["C"], "B": ["A"], "C": ["B"]}
    order2, levels2 = resolve_build_order(pkgs2, deps2)
    print("Test 2 (Cycle Detection):")
    print("Build Order:", order2)  # Expected: []
    print("Levels:", levels2)  # Expected: -1