# Deterministic Package Build Order
# Uses Kahn's Topological Sort with a Min-Heap
# Standard library only

import heapq


def build_order(packages, dependencies):
    """
    Given:
        packages: iterable of package names
        dependencies: iterable of (package, prerequisite) pairs
                       meaning prerequisite must be built first

    Returns:
        (build_order, levels)

        If a cycle exists:
            ([], -1)
    """

    # Build graph and indegree table
    graph = {package: [] for package in packages}
    indegree = {package: 0 for package in packages}

    # Add dependencies
    for package, prerequisite in dependencies:
        # Ensure all mentioned packages exist
        if package not in graph:
            graph[package] = []
            indegree[package] = 0

        if prerequisite not in graph:
            graph[prerequisite] = []
            indegree[prerequisite] = 0

        graph[prerequisite].append(package)
        indegree[package] += 1

    # Sort adjacency lists for deterministic processing
    for package in graph:
        graph[package].sort()

    # Min-heap contains packages with no remaining prerequisites
    heap = []

    # depth[p] = longest prerequisite depth ending at p
    depth = {package: 1 for package in graph}

    for package in graph:
        if indegree[package] == 0:
            heapq.heappush(heap, package)

    order = []

    # Kahn's algorithm
    while heap:
        current = heapq.heappop(heap)
        order.append(current)

        for dependent in graph[current]:
            # The dependent can be built one level after current
            depth[dependent] = max(
                depth[dependent],
                depth[current] + 1
            )

            indegree[dependent] -= 1

            if indegree[dependent] == 0:
                heapq.heappush(heap, dependent)

    # If not all packages were processed, a cycle exists
    if len(order) != len(graph):
        return [], -1

    # Maximum dependency depth
    levels = max(depth.values(), default=0)

    return order, levels


def main():
    # Example input
    packages = [
        "app",
        "api",
        "db",
        "auth",
        "utils",
        "config"
    ]

    # (package, prerequisite)
    dependencies = [
        ("app", "api"),
        ("app", "auth"),
        ("api", "db"),
        ("api", "utils"),
        ("auth", "config")
    ]

    order, levels = build_order(packages, dependencies)

    print("Build Order:", order)
    print("Dependency Levels:", levels)


if __name__ == "__main__":
    main()