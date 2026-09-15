# Dependency Build Planner
# Deterministic build order using Kahn's algorithm with a min-heap.
# Also tracks the longest prerequisite depth (number of dependency levels).
#
# Input:
#   packages: iterable of package names
#   dependencies: iterable of (package, prerequisite) pairs
#
# Output:
#   (build_order, levels)
#
# If a cycle exists:
#   ([], -1)


import heapq


def dependency_build_planner(packages, dependencies):
    """
    Produce a deterministic valid build order and dependency levels.

    A dependency (package, prerequisite) means:
        prerequisite must be built before package.

    Returns:
        (build_order, levels)

    Where:
        build_order = deterministic topological ordering
        levels      = maximum dependency depth
                      (0 for packages with no prerequisites)

    If a cycle exists:
        ([], -1)
    """

    # Remove duplicates and sort so the result is deterministic.
    packages = sorted(set(packages))

    # Build graph:
    # prerequisite -> packages that depend on it
    graph = {package: [] for package in packages}
    indegree = {package: 0 for package in packages}

    # Add dependencies.
    for package, prerequisite in dependencies:
        # Both packages must exist in the package list.
        if package not in graph or prerequisite not in graph:
            raise ValueError(
                "Every package in dependencies must be present in packages."
            )

        graph[prerequisite].append(package)
        indegree[package] += 1

    # Sort adjacency lists for deterministic processing.
    for package in graph:
        graph[package].sort()

    # Min-heap ensures lexicographically smallest available package
    # is always selected first.
    heap = []

    for package in packages:
        if indegree[package] == 0:
            heapq.heappush(heap, package)

    # depth[p] = longest prerequisite depth before building p.
    # A package with no prerequisite has depth 0.
    depth = {package: 0 for package in packages}

    build_order = []

    # Kahn's topological sorting algorithm.
    while heap:
        current = heapq.heappop(heap)
        build_order.append(current)

        for dependent in graph[current]:
            # If current is a prerequisite of dependent,
            # dependent can now have its indegree reduced.
            indegree[dependent] -= 1

            # Track the longest prerequisite chain.
            depth[dependent] = max(
                depth[dependent],
                depth[current] + 1
            )

            # All prerequisites are now satisfied.
            if indegree[dependent] == 0:
                heapq.heappush(heap, dependent)

    # If not all packages were processed, a cycle exists.
    if len(build_order) != len(packages):
        return [], -1

    # Number of dependency levels.
    # No dependencies -> level 0.
    levels = max(depth.values(), default=0)

    return build_order, levels


# ---------------------------------------------------------
# Example
# ---------------------------------------------------------

if __name__ == "__main__":
    packages = [
        "app",
        "db",
        "api",
        "auth",
        "config"
    ]

    dependencies = [
        ("app", "api"),
        ("app", "auth"),
        ("api", "db"),
        ("auth", "config")
    ]

    order, levels = dependency_build_planner(
        packages,
        dependencies
    )

    print("Build Order:", order)
    print("Dependency Levels:", levels)

    # Example with a cycle.
    cyclic_packages = ["A", "B", "C"]
    cyclic_dependencies = [
        ("B", "A"),
        ("C", "B"),
        ("A", "C")
    ]

    order, levels = dependency_build_planner(
        cyclic_packages,
        cyclic_dependencies
    )

    print("Cyclic Build Order:", order)
    print("Cyclic Dependency Levels:", levels)