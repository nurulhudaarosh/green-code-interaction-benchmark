import heapq
from collections import defaultdict


def resolve_build_order(dependencies: list[tuple[str, str]]) -> tuple[list[str], int]:
    """
    Resolves dependency build order deterministically using Kahn's algorithm with a Min-Heap,
    correctly tracking the longest prerequisite depth (levels).
    
    :param dependencies: List of (prerequisite, package) tuples.
    :return: A tuple of (build_order, number_of_levels). Returns ([], -1) if a cycle exists.
    """
    nodes = set()
    for prereq, pkg in dependencies:
        nodes.add(prereq)
        nodes.add(pkg)

    if not nodes:
        return [], 0

    graph = defaultdict(list)
    in_degree = {node: 0 for node in nodes}

    for prereq, pkg in dependencies:
        graph[prereq].append(pkg)
        in_degree[pkg] += 1

    # Depth tracks the longest path length to reach each node (1-based level)
    depth = {node: 1 for node in nodes}

    # Min-heap for deterministic tie-breaking (lexicographical order)
    heap = [node for node, deg in in_degree.items() if deg == 0]
    heapq.heapify(heap)

    build_order = []

    while heap:
        curr = heapq.heappop(heap)
        build_order.append(curr)

        for neighbor in graph[curr]:
            # Propagate the maximum prerequisite depth path
            if depth[curr] + 1 > depth[neighbor]:
                depth[neighbor] = depth[curr] + 1

            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    # Cycle check
    if len(build_order) < len(nodes):
        return [], -1

    max_levels = max(depth.values()) if depth else 0
    return build_order, max_levels


# Verification & Test Cases
if __name__ == "__main__":
    # Test Case 1: Demonstrating correct max depth resolution with tie-breaking
    # Chain 1: B -> X (length 2)
    # Chain 2: A -> C -> X -> Y (length 4)
    deps_defect_test = [
        ("B", "X"),
        ("A", "C"),
        ("C", "X"),
        ("X", "Y"),
    ]
    order, levels = resolve_build_order(deps_defect_test)
    print("Test 1 Order:", order)   # ['A', 'B', 'C', 'X', 'Y']
    print("Test 1 Levels:", levels) # 4 (A=1, C=2, X=3, Y=4)

    # Test Case 2: Cycle Detection
    deps_cycle = [("A", "B"), ("B", "C"), ("C", "A")]
    order_c, levels_c = resolve_build_order(deps_cycle)
    print("Test 2 (Cycle) Order:", order_c)   # []
    print("Test 2 (Cycle) Levels:", levels_c) # -1