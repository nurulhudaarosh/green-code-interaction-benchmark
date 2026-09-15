import heapq
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Union


def resolve_build_order(
    dependencies: List[Tuple[str, str]], 
    include_summary: bool = False
) -> Union[Tuple[List[str], int], Tuple[List[str], int, Dict[str, Any]]]:
    """
    Resolves dependency build order deterministically using Kahn's algorithm with a Min-Heap,
    tracking longest prerequisite depth and optional execution operational metrics.

    :param dependencies: List of (prerequisite, package) tuples.
    :param include_summary: If True, returns an additional operation_summary dictionary.
    :return: (build_order, number_of_levels) or (build_order, number_of_levels, operation_summary)
    """
    # 1. Collect all unique nodes
    nodes = set()
    for prereq, pkg in dependencies:
        nodes.add(prereq)
        nodes.add(pkg)

    # Operational metrics tracking
    metrics = {
        "nodes_processed": 0,
        "edges_evaluated": 0,
        "heap_push_operations": 0,
        "heap_pop_operations": 0,
        "cycle_detected": False,
    }

    if not nodes:
        if include_summary:
            return [], 0, metrics
        return [], 0

    # 2. Build graph and in-degree map
    graph = defaultdict(list)
    in_degree = {node: 0 for node in nodes}

    for prereq, pkg in dependencies:
        graph[prereq].append(pkg)
        in_degree[pkg] += 1

    # Depth tracks the longest path length to reach each node (1-based level)
    depth = {node: 1 for node in nodes}

    # 3. Min-heap initialization for deterministic tie-breaking
    initial_heap_nodes = [node for node, deg in in_degree.items() if deg == 0]
    heapq.heapify(initial_heap_nodes)
    
    heap = initial_heap_nodes
    metrics["heap_push_operations"] += len(heap)

    build_order = []

    # 4. Kahn's Algorithm execution
    while heap:
        curr = heapq.heappop(heap)
        metrics["heap_pop_operations"] += 1
        metrics["nodes_processed"] += 1
        build_order.append(curr)

        for neighbor in graph[curr]:
            metrics["edges_evaluated"] += 1
            
            # Propagate maximum prerequisite depth path
            if depth[curr] + 1 > depth[neighbor]:
                depth[neighbor] = depth[curr] + 1

            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)
                metrics["heap_push_operations"] += 1

    # 5. Cycle Detection Check
    if len(build_order) < len(nodes):
        metrics["cycle_detected"] = True
        if include_summary:
            return [], -1, metrics
        return [], -1

    max_levels = max(depth.values()) if depth else 0

    if include_summary:
        return build_order, max_levels, metrics
    return build_order, max_levels


# Verification & Usage
if __name__ == "__main__":
    deps = [
        ("B", "X"),
        ("A", "C"),
        ("C", "X"),
        ("X", "Y"),
    ]

    # Standard call (Original Signature)
    order, levels = resolve_build_order(deps)
    print("Default Output:")
    print("  Build Order:", order)
    print("  Levels:", levels)

    # Extended call with operational summary
    order, levels, summary = resolve_build_order(deps, include_summary=True)
    print("\nWith Operational Summary:")
    print("  Build Order:", order)
    print("  Levels:", levels)
    print("  Summary:", summary)