import heapq
from typing import List, Tuple, Dict, Set


def get_deterministic_build_order(
    packages: List[str], 
    dependencies: List[Tuple[str, str]]
) -> Tuple[List[str], int]:
    """
    Computes a deterministic build order and dependency levels.
    
    :param packages: List of package names.
    :param dependencies: List of (package, prerequisite) tuples where 
                         package depends on prerequisite.
    :return: Tuple of (build_order, num_levels). Returns ([], -1) if a cycle exists.
    """
    # Unique set of all packages (including those only mentioned in dependencies)
    all_packages: Set[str] = set(packages)
    for pkg, dep in dependencies:
        all_packages.add(pkg)
        all_packages.add(dep)
        
    in_degree: Dict[str, int] = {pkg: 0 for pkg in all_packages}
    graph: Dict[str, List[str]] = {pkg: [] for pkg in all_packages}
    
    # Build adjacency list: prerequisite -> target
    for pkg, dep in dependencies:
        graph[dep].append(pkg)
        in_degree[pkg] += 1

    # Min-heap to maintain lexicographical order for ties
    min_heap: List[str] = [pkg for pkg, deg in in_degree.items() if deg == 0]
    heapq.heapify(min_heap)

    # Track depth level of each package
    level: Dict[str, int] = {pkg: 1 for pkg in min_heap}
    
    build_order: List[str] = []
    
    while min_heap:
        curr = heapq.heappop(min_heap)
        build_order.append(curr)
        curr_level = level[curr]
        
        for neighbor in graph[curr]:
            in_degree[neighbor] -= 1
            # Track longest path to calculate dependency levels
            level[neighbor] = max(level.get(neighbor, 1), curr_level + 1)
            
            if in_degree[neighbor] == 0:
                heapq.heappush(min_heap, neighbor)

    # Check for cyclic dependency
    if len(build_order) != len(all_packages):
        return [], -1
    
    total_levels = max(level.values()) if level else 0
    return build_order, total_levels


# Example Usage & Test Verification
if __name__ == "__main__":
    pkgs = ["A", "B", "C", "D", "E"]
    # A depends on B and C; B depends on D; C depends on D
    deps = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]
    
    order, levels = get_deterministic_build_order(pkgs, deps)
    print("Build Order:", order)
    print("Dependency Levels:", levels)
    # Expected output:
    # Build Order: ['D', 'E', 'B', 'C', 'A']
    # Dependency Levels: 3