class DSU:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n if n > 0 else []
        self.num_components = n
        self.max_size = 1 if n > 0 else 0

    def find(self, i: int) -> int:
        path = []
        while self.parent[i] != i:
            path.append(i)
            i = self.parent[i]
        for node in path:
            self.parent[node] = i
        return i

    def union(self, i: int, j: int) -> bool:
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i != root_j:
            # Union by size
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            
            if self.size[root_i] > self.max_size:
                self.max_size = self.size[root_i]
                
            self.num_components -= 1
            return True  # Successful merge
        return False  # Endpoints already in same component


def analyze_graph_thresholds(
    n: int, 
    edges: list[tuple[int, int, float]], 
    queries: list[float],
    include_summary: bool = False
):
    """
    Evaluates connected components and maximum component size for edge weight thresholds.

    :param n: Number of vertices (0 to n-1)
    :param edges: List of tuples (u, v, weight)
    :param queries: List of weight thresholds q
    :param include_summary: If True, returns a tuple (results, operation_summary)
    :return: List of tuples (num_components, max_component_size) or tuple with operation_summary
    """
    sorted_edges = sorted(edges, key=lambda x: x[2])
    sorted_queries = sorted(enumerate(queries), key=lambda x: x[1])
    
    dsu = DSU(n)
    results = [(0, 0)] * len(queries)
    
    edge_idx = 0
    num_edges = len(sorted_edges)
    
    # Track deterministic operation counts
    successful_unions = 0
    redundant_edges = 0
    
    for original_idx, q in sorted_queries:
        while edge_idx < num_edges and sorted_edges[edge_idx][2] <= q:
            u, v, _ = sorted_edges[edge_idx]
            merged = dsu.union(u, v)
            if merged:
                successful_unions += 1
            else:
                redundant_edges += 1
            edge_idx += 1
            
        results[original_idx] = (dsu.num_components, dsu.max_size)
    
    if include_summary:
        operation_summary = {
            "total_edges_processed": edge_idx,
            "successful_unions": successful_unions,
            "redundant_edges": redundant_edges,
            "queries_processed": len(queries)
        }
        return results, operation_summary
        
    return results


# Example Usage
if __name__ == "__main__":
    num_nodes = 5
    graph_edges = [
        (0, 1, 3.0),
        (1, 2, 1.0),
        (2, 3, 5.0),
        (3, 4, 2.0),
        (0, 2, 2.5)  # Creates a cycle when w >= 3.0
    ]
    thresholds = [0.5, 1.5, 3.0, 5.0]
    
    # 1. Standard usage (backward compatible)
    res_only = analyze_graph_thresholds(num_nodes, graph_edges, thresholds)
    print("Standard Output:", res_only)
    
    # 2. Output with operation summary enabled
    res, summary = analyze_graph_thresholds(num_nodes, graph_edges, thresholds, include_summary=True)
    print("\nResults:", res)
    print("Operation Summary:", summary)