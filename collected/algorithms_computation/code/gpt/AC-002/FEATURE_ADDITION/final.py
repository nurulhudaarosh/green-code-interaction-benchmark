# Dependency Build Planner
#
# Original problem:
# Given packages and prerequisite dependencies, produce a deterministic
# valid build order and the number of dependency levels.
#
# A dependency (package, prerequisite) means:
#     prerequisite must be built before package.
#
# If a cycle exists:
#     return ([], -1)
#
# Algorithm:
#     Kahn's topological sorting with a min-heap.
#     The min-heap provides deterministic tie handling.
#     Longest prerequisite depth is tracked to calculate dependency levels.
#
# New feature:
#     When include_operation_summary=True, return:
#         (build_order, levels, operation_summary)
#
#     Otherwise, preserve the original output exactly:
#         (build_order, levels)
#
# operation_summary:
#     A deterministic count of the major computational decisions/operations
#     performed by the algorithm.
#
# Standard library only.


import heapq


def dependency_build_planner(
    packages,
    dependencies,
    include_operation_summary=False
):
    """
    Produce a deterministic valid build order and dependency levels.

    Parameters
    ----------
    packages:
        Iterable of package names.

    dependencies:
        Iterable of (package, prerequisite) pairs.
        The prerequisite must be built before the package.

    include_operation_summary:
        If False, preserve the original two-field result:
            (build_order, levels)

        If True, return:
            (build_order, levels, operation_summary)

    Returns
    -------
    Without operation summary:
        (build_order, levels)

    With operation summary:
        (build_order, levels, operation_summary)

    If a cycle exists:
        Without summary:
            ([], -1)

        With summary:
            ([], -1, operation_summary)
    """

    # ---------------------------------------------------------
    # Operation counter
    # ---------------------------------------------------------
    #
    # Count major algorithmic operations deterministically:
    #
    # 1. Each dependency processed while constructing the graph.
    # 2. Each package selected from the min-heap.
    # 3. Each dependent edge processed during Kahn's algorithm.
    # 4. Each package inserted into the heap.
    #
    # These are algorithmic decisions/operations rather than
    # implementation-specific low-level operations.
    operation_count = 0

    # Remove duplicate packages and sort them.
    # Sorting guarantees deterministic initial ordering.
    packages = sorted(set(packages))

    # Build graph:
    # prerequisite -> packages that depend on it
    graph = {package: [] for package in packages}
    indegree = {package: 0 for package in packages}

    # ---------------------------------------------------------
    # Build dependency graph
    # ---------------------------------------------------------
    for package, prerequisite in dependencies:
        if package not in graph or prerequisite not in graph:
            raise ValueError(
                "Every package in dependencies must be present in packages."
            )

        graph[prerequisite].append(package)
        indegree[package] += 1

        operation_count += 1

    # Sort adjacency lists for deterministic traversal.
    for package in graph:
        graph[package].sort()

    # ---------------------------------------------------------
    # Initialize min-heap with packages having no prerequisites.
    # ---------------------------------------------------------
    heap = []

    for package in packages:
        if indegree[package] == 0:
            heapq.heappush(heap, package)
            operation_count += 1

    # depth[p] is the longest prerequisite depth before p.
    #
    # A package with no prerequisites has depth 0.
    depth = {package: 0 for package in packages}

    build_order = []

    # ---------------------------------------------------------
    # Kahn's topological sorting
    # ---------------------------------------------------------
    while heap:
        # The smallest available package is always selected.
        current = heapq.heappop(heap)
        build_order.append(current)

        operation_count += 1

        for dependent in graph[current]:
            # Remove current prerequisite.
            indegree[dependent] -= 1

            # Update longest prerequisite depth.
            depth[dependent] = max(
                depth[dependent],
                depth[current] + 1
            )

            operation_count += 1

            # All prerequisites have now been satisfied.
            if indegree[dependent] == 0:
                heapq.heappush(heap, dependent)
                operation_count += 1

    # ---------------------------------------------------------
    # Cycle detection
    # ---------------------------------------------------------
    if len(build_order) != len(packages):
        if include_operation_summary:
            operation_summary = {
                "major_operations": operation_count
            }

            return [], -1, operation_summary

        return [], -1

    # ---------------------------------------------------------
    # Calculate dependency levels
    # ---------------------------------------------------------
    #
    # No dependencies:
    #     levels = 0
    #
    # A -> B:
    #     A = 0
    #     B = 1
    #     levels = 1
    levels = max(depth.values(), default=0)

    # ---------------------------------------------------------
    # Preserve the original output when the feature is disabled.
    # ---------------------------------------------------------
    if not include_operation_summary:
        return build_order, levels

    # New optional output.
    operation_summary = {
        "major_operations": operation_count
    }

    return build_order, levels, operation_summary


# =============================================================
# Example 1: Original behavior
# =============================================================

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

    # Feature disabled:
    # Output format remains exactly the original:
    #     (build_order, levels)
    result = dependency_build_planner(
        packages,
        dependencies
    )

    print("Original Output:")
    print(result)


    # =========================================================
    # Example 2: New operation_summary feature enabled
    # =========================================================

    result_with_summary = dependency_build_planner(
        packages,
        dependencies,
        include_operation_summary=True
    )

    print("\nOutput With Operation Summary:")
    print(result_with_summary)


    # =========================================================
    # Example 3: Cycle
    # =========================================================

    cyclic_packages = [
        "A",
        "B",
        "C"
    ]

    cyclic_dependencies = [
        ("B", "A"),
        ("C", "B"),
        ("A", "C")
    ]

    # Original cycle output remains:
    #     ([], -1)
    cyclic_result = dependency_build_planner(
        cyclic_packages,
        cyclic_dependencies
    )

    print("\nCyclic Output:")
    print(cyclic_result)


    # With the new feature:
    #     ([], -1, operation_summary)
    cyclic_result_with_summary = dependency_build_planner(
        cyclic_packages,
        cyclic_dependencies,
        include_operation_summary=True
    )

    print("\nCyclic Output With Operation Summary:")
    print(cyclic_result_with_summary)