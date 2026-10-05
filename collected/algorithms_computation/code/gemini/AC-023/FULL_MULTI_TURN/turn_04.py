class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_component_size = 1 if n > 0 else 0

    def find(self, i: int) -> int:
        path = []
        while self.parent[i] != i:
            path.append(i)
            i = self.parent[i]
        for node in path:
            self.parent[node] = i
        return i

    def union(self, i: int, j: int) -> tuple[bool, int]:
        root_i = self.find(i)
        root_j = self.find(j)
        find_ops = 2
        
        if root_i != root_j:
            # Deterministic union by size; tie-break by smaller root index
            if self.size[root_i] < self.size[root_j] or (
                self.size[root_i] == self.size[root_j] and root_i > root_j
            ):
                root_i, root_j = root_j, root_i
            
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            
            if self.size[root_i] > self.max_component_size:
                self.max_component_size = self.size[root_i]
                
            self.num_components -= 1
            return True, find_ops
        return False, find_ops


def solve_threshold_queries(
    n: int, 
    edges: list[tuple[int, int, int]], 
    queries: list[int],
    include_summary: bool = False
) -> list[tuple[int, int]] | dict:
    ops_edge_canonicalizations = len(edges)
    ops_union_evaluations = 0
    ops_successful_merges = 0
    ops_find_calls = 0

    # Canonicalize and deterministically sort edges by (weight, min(u, v), max(u, v))
    sorted_edges = sorted(
        [(w, min(u, v), max(u, v)) for u, v, w in edges],
        key=lambda x: (x[0], x[1], x[2])
    )
    
    # Deterministically sort queries by (threshold, original_index)
    indexed_queries = sorted(
        enumerate(queries), 
        key=lambda x: (x[1], x[0])
    )
    
    dsu = UnionFind(n)
    results = [(0, 0)] * len(queries)
    
    edge_idx = 0
    num_edges = len(sorted_edges)
    
    for orig_idx, q in indexed_queries:
        # Add all edges with weight <= q in deterministic order
        while edge_idx < num_edges and sorted_edges[edge_idx][0] <= q:
            _, u, v = sorted_edges[edge_idx]
            merged, find_ops = dsu.union(u, v)
            ops_union_evaluations += 1
            ops_find_calls += find_ops
            if merged:
                ops_successful_merges += 1
            edge_idx += 1
            
        results[orig_idx] = (dsu.num_components, dsu.max_component_size)
        
    if include_summary:
        return {
            "results": results,
            "operation_summary": {
                "edges_processed": edge_idx,
                "canonicalization_ops": ops_edge_canonicalizations,
                "union_evaluations": ops_union_evaluations,
                "successful_merges": ops_successful_merges,
                "find_operations": ops_find_calls,
                "queries_evaluated": len(queries)
            }
        }
        
    return results


# --- Unit Tests ---

def test_boundary_cases():
    # 1. Zero Vertices (n = 0)
    res_zero = solve_threshold_queries(0, [], [0, 5])
    assert res_zero == [(0, 0), (0, 0)], f"Failed on n=0: {res_zero}"

    # 2. Single Vertex, No Edges (n = 1)
    res_single = solve_threshold_queries(1, [], [-10, 0, 10])
    assert res_single == [(1, 1), (1, 1), (1, 1)], f"Failed on n=1: {res_single}"

    # 3. No Edges (n = 5)
    res_no_edges = solve_threshold_queries(5, [], [1, 100])
    assert res_no_edges == [(5, 1), (5, 1)], f"Failed on no edges: {res_no_edges}"

    # 4. No Queries
    res_no_queries = solve_threshold_queries(3, [(0, 1, 2)], [])
    assert res_no_queries == [], f"Failed on no queries: {res_no_queries}"

    # 5. Queries Below Min / Above Max Edge Weight
    edges = [(0, 1, 5), (1, 2, 10)]
    res_out_of_bounds = solve_threshold_queries(3, edges, [0, 5, 20])
    assert res_out_of_bounds == [(3, 1), (2, 2), (1, 3)], f"Failed out of bounds: {res_out_of_bounds}"

    # 6. Self-Loops and Duplicate Edges
    edges_loops = [(0, 0, 1), (0, 1, 2), (0, 1, 2)]
    res_loops = solve_threshold_queries(2, edges_loops, [1, 2])
    assert res_loops == [(2, 1), (1, 2)], f"Failed on self-loops/duplicates: {res_loops}"

    # 7. Summary Flag with Boundary Inputs
    res_summary = solve_threshold_queries(0, [], [1], include_summary=True)
    assert res_summary["results"] == [(0, 0)]
    assert res_summary["operation_summary"]["queries_evaluated"] == 1

    print("All boundary tests passed successfully!")


if __name__ == "__main__":
    test_boundary_cases()