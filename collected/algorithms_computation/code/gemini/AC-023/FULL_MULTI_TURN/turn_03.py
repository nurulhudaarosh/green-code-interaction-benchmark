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
        """
        Unions two sets deterministically.
        Returns (was_merged, find_ops_performed).
        """
        root_i = self.find(i)
        root_j = self.find(j)
        find_ops = 2  # Evaluated find for both i and j
        
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
    """
    Problem Restatement & Requirements:
    - Input: Number of vertices n (indexed 0 to n-1), a list of edges (u, v, w),
      and a list of weight threshold queries q.
    - Query Filtering: For each threshold q, consider only edges with weight w <= q.
    - Required Original Output: A list of pairs (num_components, max_component_size)
      for each query in original query order.
    - Added Feature (`include_summary`): When set to True, returns a dict containing:
        - "results": The original list of (num_components, max_component_size) pairs.
        - "operation_summary": Deterministic counts of key computational decisions/operations
          (sorted edge canonicalizations, total union evaluations, successful component merges,
          and total find operations).
      When `include_summary` is False (default), returns exactly the original list of tuples.
    """
    # Track operations for operation_summary feature
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


# Example Usage & Verification:
if __name__ == "__main__":
    n = 5
    edges = [(0, 1, 2), (1, 2, 5), (2, 3, 3), (3, 4, 8)]
    queries = [1, 3, 5, 10]

    # Standard usage (Feature disabled -> returns exact original output structure)
    original_output = solve_threshold_queries(n, edges, queries)
    print("Original Output (include_summary=False):")
    print(original_output)

    # Extended usage (Feature enabled -> returns dict with results and operation summary)
    summary_output = solve_threshold_queries(n, edges, queries, include_summary=True)
    print("\nSummary Output (include_summary=True):")
    print(summary_output)