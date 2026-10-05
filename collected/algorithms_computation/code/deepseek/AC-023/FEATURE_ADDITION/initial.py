import sys

class DSU:
    __slots__ = ('parent', 'size', 'num_components', 'max_size')

    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_size = 1 if n > 0 else 0

    def find(self, x):
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        # path compression
        while self.parent[x] != root:
            nxt = self.parent[x]
            self.parent[x] = root
            x = nxt
        return root

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        # union by size
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.num_components -= 1
        if self.size[ra] > self.max_size:
            self.max_size = self.size[ra]


def solve(n, edges, queries):
    # Handle edge case
    if n == 0:
        return [[0, 0] for _ in queries]

    # Sort edges by weight
    edges_sorted = sorted(edges, key=lambda e: e[2])

    # Sort queries by threshold, keep original index
    indexed_queries = sorted(enumerate(queries), key=lambda x: x[1])

    dsu = DSU(n)
    answers = [None] * len(queries)
    ei = 0
    m = len(edges_sorted)

    for orig_idx, q in indexed_queries:
        # Add all edges with weight <= q
        while ei < m and edges_sorted[ei][2] <= q:
            u, v, _ = edges_sorted[ei]
            dsu.union(u, v)
            ei += 1
        answers[orig_idx] = [dsu.num_components, dsu.max_size]

    return answers


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    pos = 0
    n = int(data[pos]); pos += 1
    m = int(data[pos]); pos += 1

    edges = []
    for _ in range(m):
        u = int(data[pos]); pos += 1
        v = int(data[pos]); pos += 1
        w = int(data[pos]); pos += 1
        edges.append((u, v, w))

    qn = int(data[pos]); pos += 1
    queries = []
    for _ in range(qn):
        queries.append(int(data[pos])); pos += 1

    result = solve(n, edges, queries)
    out = []
    for comp, mx in result:
        out.append(f"{comp} {mx}")
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()