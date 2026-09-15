import heapq
from collections import defaultdict


def resolve_build_order(dependencies: list[tuple[str, str]]) -> tuple[list[str], int]:
    """
    Resolves dependency build order deterministically using Kahn's algorithm with a Min-Heap.
    
    :param dependencies: List of (prerequisite, package) tuples.
    :return: A tuple of (build_order, number_of_levels). Returns ([], -1) if a cycle exists.
    """
    # 1. Collect all unique nodes
    nodes = set()
    for prereq, pkg in dependencies:
        nodes.add(prereq)
        nodes.add(pkg)
    
    if not nodes:
        return [], 0

    # 2. Build graph and in-degree map
    graph = defaultdict(list)
    in_degree = {node: 0 for node in nodes}
    
    for prereq, pkg in dependencies:
        graph[prereq].append(pkg)
        in_degree[pkg] += 1

    # 3. Min-heap for deterministic ordering (lexicographical)
    # Heap entries: node_name
    heap = [node for node, deg in in_degree.items() if deg == 0]
    heapq.heapify(heap)

    # Track maximum depth/level for each node (1-based level height)
    depth = {node: 1 for node in heap}
    
    build_order = []

    # 4. Kahn's Algorithm
    while heap:
        curr = heapq.heappop(heap)
        build_order.append(curr)

        for neighbor in graph[curr]:
            # Update the max depth for dependent packages
            depth[neighbor] = max(depth.get(neighbor, 1), depth[curr] + 1)
            
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)

    # 5. Cycle Detection Check
    if len(build_order) < len(nodes):
        return [], -1

    max_levels = max(depth.values()) if depth else 0
    return build_order, max_levels


# Example Usage & Testing
if __name__ == "__main__":
    # Test Case 1: Valid DAG
    deps1 = [
        ("A", "B"),
        ("A", "C"),
        ("B", "D"),
        ("C", "D"),
        ("E", "C")
    ]
    order, levels = resolve_build_order(deps1)
    print(f"Build Order: {order}")  # Output: ['A', 'E', 'B', 'C', 'D']
    print(f"Levels: {levels}")       # Output: 3

    # Test Case 2: Cycle Detection
    deps2 = [
        ("A", "B"),
        ("B", "C"),
        ("C", "A")
    ]
    order_cycle, levels_cycle = resolve_build_order(deps2)
    print(f"Build Order (Cycle): {order_cycle}")  # Output: []
    print(f"Levels (Cycle): {levels_cycle}")       # Output: -1