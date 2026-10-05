import sys

class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_size = 1 if n > 0 else 0

    def find(self, x):
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
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.num_components -= 1
        if self.size[ra] > self.max_size:
            self.max_size = self.size[ra]


def solve(n, edges, queries):
    m = len(edges)
    q = len(queries)

    # Deterministic: sort edges by (weight, u, v) so tie order is fixed.
    edges_sorted = sorted(edges, key=lambda e: (e[2], e[0], e[1]))

    # Deterministic tie-break: sort queries by (threshold, original_index).
    queries_indexed = sorted((thr, i) for i, thr in enumerate(queries))

    dsu = DSU(n)
    results = [None] * q
    edge_ptr = 0

    for threshold, orig_idx in queries_indexed:
        # FIX 1: consume ALL edges with weight <= threshold BEFORE answering.
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
    queries = [int(data[idx + i]) for i in range(q)]
    results = solve(n, edges, queries)
    sys.stdout.write("\n".join(f"{c} {s}" for c, s in results) + "\n")


if __name__ == "__main__":
    main()