import heapq
from typing import Dict, List, Tuple

def get_deterministic_build_order(dependencies: Dict[str, List[str]]) -> Tuple[List[str], int]:
    """
    Computes a deterministic build order and the number of dependency levels.
    
    :param dependencies: Dictionary mapping a package to its list of direct prerequisites.
                         e.g., {'A': ['B', 'C']} means A depends on B and C.
    :return: A tuple of (build_order_list, dependency_levels_count)
             Returns ([], -1) if a dependency cycle is detected.
    """
    # Collect all unique packages (both keys and listed dependencies)
    all_packages = set(dependencies.keys())
    for prereqs in dependencies.values():
        all_packages.update(prereqs)
        
    if not all_packages:
        return [], 0

    # Initialize graph structures
    adj = {pkg: [] for pkg in all_packages}
    in_degree = {pkg: 0 for pkg in all_packages}
    depth = {pkg: 1 for pkg in all_packages}

    # Build adjacency list and compute in-degrees
    for pkg, prereqs in dependencies.items():
        in_degree[pkg] += len(prereqs)
        for prereq in prereqs:
            adj[prereq].append(pkg)

    # Priority queue (min-heap) to ensure lexicographical tie-breaking
    min_heap = [pkg for pkg, deg in in_degree.items() if deg == 0]
    heapq.heapify(min_heap)

    build_order = []

    # Kahn's algorithm using Min-Heap
    while min_heap:
        curr = heapq.heappop(min_heap)
        build_order.append(curr)

        for neighbor in adj[curr]:
            # Track longest dependency chain
            depth[neighbor] = max(depth[neighbor], depth[curr] + 1)
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(min_heap, neighbor)

    # If build_order doesn't include all packages, a cycle exists
    if len(build_order) != len(all_packages):
        return [], -1

    total_levels = max(depth.values()) if depth else 0
    return build_order, total_levels


if __name__ == "__main__":
    # Test Case 1: Standard DAG with multiple independent choices
    deps_1 = {
        "app": ["lib_a", "lib_b"],
        "lib_a": ["core"],
        "lib_b": ["core"],
        "core": []
    }
    order1, levels1 = get_deterministic_build_order(deps_1)
    print("Test 1 Result:", order1, "Levels:", levels1)
    # Expected: ['core', 'lib_a', 'lib_b', 'app'] Levels: 3

    # Test Case 2: Cyclic Dependency
    deps_2 = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"]
    }
    order2, levels2 = get_deterministic_build_order(deps_2)
    print("Test 2 Result:", order2, "Levels:", levels2)
    # Expected: [] Levels: -1