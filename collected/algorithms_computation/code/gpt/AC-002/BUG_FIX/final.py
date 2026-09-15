# Dependency Build Planner
# Deterministic Kahn Topological Sort
# Standard library only

import heapq


def dependency_build_planner(packages, dependencies):
    """
    Given packages and prerequisite dependencies, return:

        (build_order, levels)

    where:
        - build_order is a deterministic valid topological order.
        - levels is the longest prerequisite depth.

    A dependency (package, prerequisite) means:
        prerequisite must be built before package.

    If a cycle exists:
        return ([], -1)
    """

    # Initialize graph and indegree
    graph = {package: [] for package in packages}
    indegree = {package: 0 for package in packages}

    # Build the dependency graph
    for package, prerequisite in dependencies:

        # Support packages appearing only in dependencies
        if package not in graph:
            graph[package] = []
            indegree[package] = 0

        if prerequisite not in graph:
            graph[prerequisite] = []
            indegree[prerequisite] = 0

        graph[prerequisite].append(package)
        indegree[package] += 1

    # Sort adjacency lists so processing is deterministic
    for package in graph:
        graph[package].sort()

    # depth[p] = longest prerequisite chain ending at p
    depth = {package: 1 for package in graph}

    # Min-heap of currently available packages
    heap = []

    for package in graph:
        if indegree[package] == 0:
            heapq.heappush(heap, package)

    build_order = []

    # Kahn's algorithm
    while heap:
        # Always choose lexicographically smallest available package
        current = heapq.heappop(heap)
        build_order.append(current)

        for dependent in graph[current]:
            # Longest prerequisite depth
            depth[dependent] = max(
                depth[dependent],
                depth[current] + 1
            )

            indegree[dependent] -= 1

            # All prerequisites are now satisfied
            if indegree[dependent] == 0:
                heapq.heappush(heap, dependent)

    # If some packages were not processed, a cycle exists
    if len(build_order) != len(graph):
        return [], -1

    # Number of dependency levels
    levels = max(depth.values(), default=0)

    return build_order, levels


def main():
    # Small valid example demonstrating deterministic tie handling
    packages = ["A", "B", "C", "D"]

    # (package, prerequisite)
    dependencies = [
        ("C", "A"),
        ("C", "B"),
        ("D", "A")
    ]

    order, levels = dependency_build_planner(
        packages,
        dependencies
    )

    print("Build Order:", order)
    print("Dependency Levels:", levels)


if __name__ == "__main__":
    main()