import sys
from bisect import bisect_right

class DSU:
    __slots__ = ("parent", "size", "components", "largest")

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = 1 if n > 0 else 0

    def find(self, x: int) -> int:
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        # Union by size
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        if self.size[ra] > self.largest:
            self.largest = self.size[ra]


def solve() -> None:
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

    edges.sort(key=lambda x: x[0])
    weights = [e[0] for e in edges]

    q = int(next(it))
    queries = []
    for i in range(q):
        threshold = int(next(it))
        queries.append((threshold, i))

    queries.sort(key=lambda x: x[0])

    dsu = DSU(n)
    answers = [None] * q
    edge_idx = 0

    for threshold, original_idx in queries:
        # Add every edge whose weight <= threshold
        limit = bisect_right(weights, threshold)
        while edge_idx < limit:
            _, u, v = edges[edge_idx]
            dsu.union(u, v)
            edge_idx += 1

        answers[original_idx] = (dsu.components, dsu.largest)

    out = []
    for comp, largest in answers:
        out.append(f"{comp} {largest}")
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()