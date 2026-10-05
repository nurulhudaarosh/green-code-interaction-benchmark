import sys

class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.max_size = 1 if n > 0 else 0

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        if self.size[ra] > self.max_size:
            self.max_size = self.size[ra]


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    it = iter(data)
    n = int(next(it))
    m = int(next(it))

    edges = []
    for _ in range(m):
        u = int(next(it)) - 1
        v = int(next(it)) - 1
        w = int(next(it))
        edges.append((w, u, v))

    q = int(next(it))
    queries = []
    for i in range(q):
        threshold = int(next(it))
        queries.append((threshold, i))

    edges.sort(key=lambda x: x[0])
    queries.sort(key=lambda x: x[0])

    dsu = DSU(n)
    answers = [None] * q

    e_idx = 0
    for threshold, original_idx in queries:
        while e_idx < m and edges[e_idx][0] <= threshold:
            _, u, v = edges[e_idx]
            dsu.union(u, v)
            e_idx += 1
        answers[original_idx] = (dsu.components, dsu.max_size)

    out = []
    for comp, mx in answers:
        out.append(f"{comp} {mx}")
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()