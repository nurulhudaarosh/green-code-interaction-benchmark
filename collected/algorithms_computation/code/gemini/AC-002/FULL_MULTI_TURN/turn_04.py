import heapq
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Union


def resolve_build_order(
    dependencies: List[Tuple[str, str]], 
    include_summary: bool = False
) -> Union[Tuple[List[str], int], Tuple[List[str], int, Dict[str, Any]]]:
    """
    Resolves dependency build order deterministically using Kahn's algorithm with a Min-Heap.
    Handles duplicate dependency pairs, self-loops, and deterministic tie-breaking.

    :param dependencies: List of (prerequisite, package) tuples.
    :param include_summary: If True, returns an additional operation_summary dictionary.
    :return: (build_order, number_of_levels) or (build_order, number_of_levels, operation_summary)
    """
    metrics = {
        "nodes_processed": 0,
        "edges_evaluated": 0,
        "heap_push_operations": 0,
        "heap_pop_operations": 0,
        "cycle_detected": False,
    }

    if not dependencies:
        if include_summary:
            return [], 0, metrics
        return [], 0

    # 1. Deduplicate dependency edges to handle repeated values
    unique_dependencies = set(dependencies)

    # 2. Collect unique nodes & check for self-loops
    nodes = set()
    for prereq, pkg in unique_dependencies:
        if prereq == pkg:  # Direct self-loop cycle
            metrics["cycle_detected"] = True
            if include_summary:
                return [], -1, metrics
            return [], -1
        nodes.add(prereq)
        nodes.add(pkg)

    # 3. Build graph and in-degree map from deduplicated edges
    graph = defaultdict(list)
    in_degree = {node: 0 for node in nodes}

    for prereq, pkg in unique_dependencies:
        graph[prereq].append(pkg)
        in_degree[pkg] += 1

    # Depth tracks longest prerequisite path (1-based height)
    depth = {node: 1 for node in nodes}

    # 4. Initialize Min-Heap with zero-in-degree nodes
    initial_heap = [node for node, deg in in_degree.items() if deg == 0]
    heapq.heapify(initial_heap)
    
    heap = initial_heap
    metrics["heap_push_operations"] += len(heap)

    build_order = []

    # 5. Kahn's Topological Sort with Min-Heap
    while heap:
        curr = heapq.heappop(heap)
        metrics["heap_pop_operations"] += 1
        metrics["nodes_processed"] += 1
        build_order.append(curr)

        for neighbor in graph[curr]:
            metrics["edges_evaluated"] += 1
            
            # Propagate maximum depth along prerequisite paths
            if depth[curr] + 1 > depth[neighbor]:
                depth[neighbor] = depth[curr] + 1

            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, neighbor)
                metrics["heap_push_operations"] += 1

    # 6. Cycle Detection Check
    if len(build_order) < len(nodes):
        metrics["cycle_detected"] = True
        if include_summary:
            return [], -1, metrics
        return [], -1

    max_levels = max(depth.values()) if depth else 0

    if include_summary:
        return build_order, max_levels, metrics
    return build_order, max_levels


# Automated Test Suite
def run_tests():
    # Test 1: Deduplication of repeated dependency pairs
    deps_duplicates = [
        ("A", "B"), ("A", "B"), ("A", "B"),
        ("B", "C"), ("B", "C")
    ]
    order, levels = resolve_build_order(deps_duplicates)
    assert order == ["A", "B", "C"], f"Expected ['A', 'B', 'C'], got {order}"
    assert levels == 3, f"Expected 3, got {levels}"

    # Test 2: Self-loop detection
    deps_self_loop = [("A", "B"), ("B", "B")]
    order_sl, levels_sl = resolve_build_order(deps_self_loop)
    assert order_sl == [] and levels_sl == -1, "Failed self-loop cycle detection"

    # Test 3: Complex deterministic tie-breaking with multiple levels
    # Available base nodes at start: Z, M, A -> Should process in order A, M, Z
    deps_ties = [
        ("Z", "X"),
        ("M", "X"),
        ("A", "X"),
        ("X", "B"),
        ("X", "A_dep")
    ]
    order_ties, levels_ties = resolve_build_order(deps_ties)
    assert order_ties == ["A", "M", "Z", "X", "A_dep", "B"], f"Tie-break order incorrect: {order_ties}"
    assert levels_ties == 3, f"Expected 3 levels, got {levels_ties}"

    # Test 4: Operational summary verification
    order_s, levels_s, summary = resolve_build_order(deps_duplicates, include_summary=True)
    assert summary["nodes_processed"] == 3
    assert summary["edges_evaluated"] == 2
    assert not summary["cycle_detected"]

    print("All tests passed successfully!")


if __name__ == "__main__":
    run_tests()