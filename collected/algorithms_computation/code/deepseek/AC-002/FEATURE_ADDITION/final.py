"""
Dependency Build Planner

Problem: Given packages and prerequisite dependencies, produce:
1. A deterministic valid build order (topological sort).
2. The number of dependency levels (longest chain length).
3. If a cycle exists, return an empty order and -1 for levels.

Additional Feature: Return an `operation_summary` field containing a useful 
deterministic summary of the computation. This summary reports the number of 
major computational decisions/operations made by the algorithm, including:
- Total nodes processed
- Total edges processed
- Number of heap push operations
- Number of heap pop operations
- Maximum depth computed

All original fields and requirements remain unchanged when the feature is 
disabled or not requested.
"""

import heapq
from collections import defaultdict

def build_order_and_levels(packages, dependencies, include_summary=False):
    """
    packages: list of package names (strings)
    dependencies: list of tuples (package, prerequisite)
                  meaning prerequisite must be built before package.
    include_summary: bool, if True return operation_summary dict
    
    Returns: 
        If include_summary is False: (build_order_list, levels_int)
        If include_summary is True: (build_order_list, levels_int, operation_summary_dict)
    """
    # Initialize operation counters
    ops = {
        'nodes_processed': 0,
        'edges_processed': 0,
        'heap_push_ops': 0,
        'heap_pop_ops': 0,
        'max_depth_computed': 0
    }
    
    # Build graph
    graph = defaultdict(list)
    in_degree = {pkg: 0 for pkg in packages}
    
    # Ensure all packages are in in_degree
    for pkg in packages:
        if pkg not in in_degree:
            in_degree[pkg] = 0
    
    for pkg, prereq in dependencies:
        if pkg not in in_degree:
            in_degree[pkg] = 0
        if prereq not in in_degree:
            in_degree[prereq] = 0
        graph[prereq].append(pkg)
        in_degree[pkg] += 1
    
    # Depth tracking: longest prerequisite chain length
    depth = {pkg: 0 for pkg in in_degree}
    
    # Min-heap for deterministic order
    heap = [pkg for pkg in in_degree if in_degree[pkg] == 0]
    heapq.heapify(heap)
    ops['heap_push_ops'] += len(heap)  # Initial heap build counts as pushes
    
    order = []
    processed = 0
    
    while heap:
        current = heapq.heappop(heap)
        ops['heap_pop_ops'] += 1
        order.append(current)
        processed += 1
        ops['nodes_processed'] += 1
        
        for neighbor in graph[current]:
            ops['edges_processed'] += 1
            # Update depth before decrementing in-degree
            new_depth = depth[current] + 1
            if new_depth > depth[neighbor]:
                depth[neighbor] = new_depth
                ops['max_depth_computed'] = max(ops['max_depth_computed'], new_depth)
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)
                ops['heap_push_ops'] += 1
    
    # Check for cycle
    if processed != len(in_degree):
        if include_summary:
            return [], -1, ops
        return [], -1
    
    # Levels = max depth + 1 (since depth is number of edges)
    max_levels = max(depth.values()) + 1 if depth else 0
    ops['max_depth_computed'] = max(ops['max_depth_computed'], max_levels - 1)
    
    if include_summary:
        return order, max_levels, ops
    
    return order, max_levels


# ========== EXAMPLE USAGE ==========
if __name__ == "__main__":
    print("=" * 60)
    print("DEPENDENCY BUILD PLANNER - WITH OPERATION SUMMARY")
    print("=" * 60)
    
    # Example 1: Simple chain
    packages1 = ["A", "B", "C", "D"]
    deps1 = [("B", "A"), ("C", "B"), ("D", "C")]
    
    print("\nExample 1: Simple chain")
    print("-" * 40)
    order1, levels1 = build_order_and_levels(packages1, deps1)
    print("Original output (no summary):")
    print(f"  Order: {order1}")
    print(f"  Levels: {levels1}")
    
    order1s, levels1s, ops1 = build_order_and_levels(packages1, deps1, include_summary=True)
    print("\nWith operation summary:")
    print(f"  Order: {order1s}")
    print(f"  Levels: {levels1s}")
    print(f"  Operation Summary: {ops1}")
    
    # Example 2: Diamond with multiple roots
    packages2 = ["A", "B", "C", "D", "E"]
    deps2 = [("C", "A"), ("C", "B"), ("D", "A"), ("E", "C"), ("E", "D")]
    
    print("\n\nExample 2: Diamond with multiple roots")
    print("-" * 40)
    order2, levels2 = build_order_and_levels(packages2, deps2)
    print("Original output (no summary):")
    print(f"  Order: {order2}")
    print(f"  Levels: {levels2}")
    
    order2s, levels2s, ops2 = build_order_and_levels(packages2, deps2, include_summary=True)
    print("\nWith operation summary:")
    print(f"  Order: {order2s}")
    print(f"  Levels: {levels2s}")
    print(f"  Operation Summary: {ops2}")
    
    # Example 3: Cycle
    packages3 = ["A", "B", "C"]
    deps3 = [("A", "B"), ("B", "C"), ("C", "A")]
    
    print("\n\nExample 3: Cycle (should return empty order and -1)")
    print("-" * 40)
    order3, levels3 = build_order_and_levels(packages3, deps3)
    print("Original output (no summary):")
    print(f"  Order: {order3}")
    print(f"  Levels: {levels3}")
    
    order3s, levels3s, ops3 = build_order_and_levels(packages3, deps3, include_summary=True)
    print("\nWith operation summary:")
    print(f"  Order: {order3s}")
    print(f"  Levels: {levels3s}")
    print(f"  Operation Summary: {ops3}")
    
    # Example 4: Disconnected with multiple roots (deterministic ordering)
    packages4 = ["Z", "Y", "X", "W"]
    deps4 = [("Y", "X"), ("Z", "X")]
    
    print("\n\nExample 4: Disconnected with multiple roots")
    print("-" * 40)
    order4, levels4 = build_order_and_levels(packages4, deps4)
    print("Original output (no summary):")
    print(f"  Order: {order4}")
    print(f"  Levels: {levels4}")
    
    order4s, levels4s, ops4 = build_order_and_levels(packages4, deps4, include_summary=True)
    print("\nWith operation summary:")
    print(f"  Order: {order4s}")
    print(f"  Levels: {levels4s}")
    print(f"  Operation Summary: {ops4}")
    
    # Example 5: Large graph to show operation summary scaling
    packages5 = [f"P{i}" for i in range(10)]
    deps5 = [(f"P{i}", f"P{i-1}") for i in range(1, 10)]
    deps5.extend([("P5", "P0"), ("P6", "P0")])  # Additional dependencies
    
    print("\n\nExample 5: Larger graph (10 nodes, chain + extra edges)")
    print("-" * 40)
    order5s, levels5s, ops5 = build_order_and_levels(packages5, deps5, include_summary=True)
    print(f"  Order (first 5): {order5s[:5]}...")
    print(f"  Levels: {levels5s}")
    print(f"  Operation Summary: {ops5}")
    
    print("\n" + "=" * 60)
    print("Note: All original fields (order, levels) are preserved.")
    print("The operation_summary is only returned when include_summary=True")
    print("=" * 60)