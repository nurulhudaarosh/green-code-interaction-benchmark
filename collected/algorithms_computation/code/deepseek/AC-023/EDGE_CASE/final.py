import sys
from bisect import bisect_right


class DSU:
    __slots__ = ("parent", "size", "components", "largest")

    def __init__(self, n: int):
        # n == 0 is valid: empty graph, no components, largest = 0.
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        # For n > 0 the minimum largest component is 1 (an isolated node).
        # For n == 0 there are no components, so largest is 0.
        self.largest = 1 if n > 0 else 0

    def find(self, x: int) -> int:
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
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

    pos = 0
    n = int(data[pos]); pos += 1
    m = int(data[pos]); pos += 1

    edges = []
    for _ in range(m):
        u = int(data[pos]) - 1; pos += 1
        v = int(data[pos]) - 1; pos += 1
        w = int(data[pos]); pos += 1
        edges.append((w, u, v))

    edges.sort(key=lambda e: e[0])
    weights = [e[0] for e in edges]

    q = int(data[pos]); pos += 1
    queries = []
    for i in range(q):
        t = int(data[pos]); pos += 1
        queries.append((t, i))

    queries.sort(key=lambda x: x[0])

    dsu = DSU(n)
    answers = [None] * q
    edge_idx = 0

    for threshold, original_idx in queries:
        # bisect_right is inclusive of edges whose weight == threshold.
        limit = bisect_right(weights, threshold)
        while edge_idx < limit:
            _, u, v = edges[edge_idx]
            dsu.union(u, v)
            edge_idx += 1
        answers[original_idx] = (dsu.components, dsu.largest)

    sys.stdout.write("\n".join(f"{c} {l}" for c, l in answers))


if __name__ == "__main__":
    solve()