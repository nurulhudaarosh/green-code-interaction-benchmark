"""
Problem: Given packages and prerequisite dependencies, produce:
1. A deterministic valid build order (topological sort using min-heap for lexicographically smallest order).
2. The number of dependency levels (longest chain length, i.e., maximum depth of prerequisites).

If a cycle exists, return an empty order and -1 for levels.

Algorithm:
- Build adjacency list and in-degree map from the dependency list.
- Use Kahn's algorithm with a min-heap (priority queue) to guarantee deterministic order.
- Track depth for each node: depth[child] = max(depth[child], depth[parent] + 1)
- If processed count < total nodes, cycle exists -> return [], -1
- Otherwise, return order and max depth (levels).
"""

import heapq
from collections import defaultdict, deque

def build_order_and_levels(packages, dependencies):
    """
    packages: list of package names (strings)
    dependencies: list of tuples (package, prerequisite)
                  meaning prerequisite must be built before package.
    Returns: (build_order_list, levels_int)
    """
    # Build graph
    graph = defaultdict(list)
    in_degree = {pkg: 0 for pkg in packages}
    
    # Ensure all packages are in in_degree (even if no deps)
    for pkg in packages:
        if pkg not in in_degree:
            in_degree[pkg] = 0
    
    for pkg, prereq in dependencies:
        # If package not in packages, add it (defensive)
        if pkg not in in_degree:
            in_degree[pkg] = 0
        if prereq not in in_degree:
            in_degree[prereq] = 0
        graph[prereq].append(pkg)
        in_degree[pkg] += 1
    
    # Depth tracking: longest prerequisite chain length (levels)
    depth = {pkg: 0 for pkg in in_degree}
    
    # Min-heap for deterministic order
    heap = [pkg for pkg in in_degree if in_degree[pkg] == 0]
    heapq.heapify(heap)
    
    order = []
    processed = 0
    
    while heap:
        current = heapq.heappop(heap)
        order.append(current)
        processed += 1
        
        for neighbor in graph[current]:
            # Update depth before decrementing in-degree
            depth[neighbor] = max(depth[neighbor], depth[current] + 1)
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)
    
    # Check for cycle
    if processed != len(in_degree):
        return [], -1
    
    # Levels = max depth + 1 (since depth is number of edges)
    max_levels = max(depth.values()) + 1 if depth else 0
    return order, max_levels


# ========== EXAMPLE USAGE ==========
if __name__ == "__main__":
    # Example 1: Simple chain
    packages1 = ["A", "B", "C", "D"]
    deps1 = [("B", "A"), ("C", "B"), ("D", "C")]
    order1, levels1 = build_order_and_levels(packages1, deps1)
    print("Example 1:")
    print("Order:", order1)      # ['A', 'B', 'C', 'D']
    print("Levels:", levels1)    # 4
    
    # Example 2: Diamond with multiple roots
    packages2 = ["A", "B", "C", "D", "E"]
    deps2 = [("C", "A"), ("C", "B"), ("D", "A"), ("E", "C"), ("E", "D")]
    order2, levels2 = build_order_and_levels(packages2, deps2)
    print("\nExample 2:")
    print("Order:", order2)      # ['A', 'B', 'C', 'D', 'E'] (lexicographically)
    print("Levels:", levels2)    # 3 (A->C->E or A->D->E)
    
    # Example 3: Cycle
    packages3 = ["A", "B", "C"]
    deps3 = [("A", "B"), ("B", "C"), ("C", "A")]
    order3, levels3 = build_order_and_levels(packages3, deps3)
    print("\nExample 3:")
    print("Order:", order3)      # []
    print("Levels:", levels3)    # -1
    
    # Example 4: Disconnected and multiple roots with deterministic ordering
    packages4 = ["Z", "Y", "X", "W"]
    deps4 = [("Y", "X"), ("Z", "X")]
    order4, levels4 = build_order_and_levels(packages4, deps4)
    print("\nExample 4:")
    print("Order:", order4)      # ['W', 'X', 'Y', 'Z'] (lexicographically, W first as isolated root)
    print("Levels:", levels4)    # 2 (X->Y or X->Z)