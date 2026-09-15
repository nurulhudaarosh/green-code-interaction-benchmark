import heapq
from typing import Dict, List, Set, Tuple

def get_build_order(packages: Set[str], dependencies: List[Tuple[str, str]]) -> Tuple[List[str], int]:
    """
    Determines a deterministic build order and the total number of dependency levels.
    
    :param packages: Set of all package names.
    :param dependencies: List of (prerequisite, dependent) pairs indicating prerequisite relations.
    :return: Tuple of (build_order_list, number_of_levels). Returns ([], -1) if a cycle is present.
    """
    # Graph structure representations
    adj_list: Dict[str, List[str]] = {p: [] for p in packages}
    in_degree: Dict[str, int] = {p: 0 for p in packages}
    level: Dict[str, int] = {p: 1 for p in packages}
    
    # Build graph topology
    for prereq, dependent in dependencies:
        if prereq in packages and dependent in packages:
            adj_list[prereq].append(dependent)
            in_degree[dependent] += 1

    # Min-heap to maintain lexicographical order for zero in-degree nodes
    min_heap: List[str] = [p for p in packages if in_degree[p] == 0]
    heapq.heapify(min_heap)
    
    build_order: List[str] = []
    max_levels = 0

    while min_heap:
        current = heapq.heappop(min_heap)
        build_order.append(current)
        
        current_level = level[current]
        if current_level > max_levels:
            max_levels = current_level
        
        for neighbor in adj_list[current]:
            in_degree[neighbor] -= 1
            # Track longest prerequisite depth
            level[neighbor] = max(level[neighbor], current_level + 1)
            
            if in_degree[neighbor] == 0:
                heapq.heappush(min_heap, neighbor)

    # If sorted count doesn't match total package count, a cycle exists
    if len(build_order) != len(packages):
        return [], -1
        
    return build_order, max_levels


# ==========================================
# Example Usage & Test Verification
# ==========================================
if __name__ == "__main__":
    # Case 1: Valid DAG
    pkgs = {"A", "B", "C", "D", "E"}
    deps = [
        ("A", "B"), # A -> B
        ("A", "C"), # A -> C
        ("B", "D"), # B -> D
        ("C", "D"), # C -> D
        ("E", "A"), # E -> A
    ]
    order, levels = get_build_order(pkgs, deps)
    print("Valid DAG Test:")
    print(f"  Build Order: {order}")   # Expected: ['E', 'A', 'B', 'C', 'D']
    print(f"  Levels:      {levels}\n") # Expected: 4 (E -> A -> B/C -> D)

    # Case 2: Cyclic Graph
    cyclic_pkgs = {"A", "B", "C"}
    cyclic_deps = [("A", "B"), ("B", "C"), ("C", "A")]
    order, levels = get_build_order(cyclic_pkgs, cyclic_deps)
    print("Cyclic Graph Test:")
    print(f"  Build Order: {order}")   # Expected: []
    print(f"  Levels:      {levels}")   # Expected: -1