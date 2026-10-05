import sys

class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_size = 1 if n > 0 else 0
    
    def find(self, x):
        # Path compression (iterative)
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root
    
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # Union by size
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.num_components -= 1
        if self.size[ra] > self.max_size:
            self.max_size = self.size[ra]


def solve(n, edges, queries):
    """
    n: number of nodes (0-indexed)
    edges: list of (u, v, w)
    queries: list of thresholds
    returns: list of [num_components, max_size] per query
    """
    m = len(edges)
    q = len(queries)
    
    # Sort edges by weight
    edges_sorted = sorted(edges, key=lambda e: e[2])
    
    # Sort queries with original index
    queries_indexed = sorted([(thr, i) for i, thr in enumerate(queries)])
    
    dsu = DSU(n)
    results = [None] * q
    edge_ptr = 0
    
    for threshold, orig_idx in queries_indexed:
        # Add all edges with weight <= threshold
        while edge_ptr < m and edges_sorted[edge_ptr][2] <= threshold:
            u, v, _ = edges_sorted[edge_ptr]
            dsu.union(u, v)
            edge_ptr += 1
        results[orig_idx] = [dsu.num_components, dsu.max_size]
    
    return results


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    idx = 0
    n = int(data[idx]); idx += 1
    m = int(data[idx]); idx += 1
    
    edges = []
    for _ in range(m):
        u = int(data[idx]); idx += 1
        v = int(data[idx]); idx += 1
        w = int(data[idx]); idx += 1
        edges.append((u, v, w))
    
    q = int(data[idx]); idx += 1
    queries = []
    for _ in range(q):
        queries.append(int(data[idx])); idx += 1
    
    results = solve(n, edges, queries)
    out = []
    for r in results:
        out.append(f"{r[0]} {r[1]}")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()