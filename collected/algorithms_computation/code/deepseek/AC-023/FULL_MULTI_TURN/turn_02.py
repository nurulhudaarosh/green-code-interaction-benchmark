import sys

class DSU:
    __slots__ = ("parent", "size")
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return 0, 0
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return 1, self.size[ra]


def solve():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    it = iter(data)
    n = int(next(it))
    m = int(next(it))

    raw_edges = []
    max_node = -1
    min_node = None
    for _ in range(m):
        u = int(next(it))
        v = int(next(it))
        w = int(next(it))
        raw_edges.append((w, u, v))
        if min_node is None or u < min_node:
            min_node = u
        if min_node is None or v < min_node:
            min_node = v
        if u > max_node:
            max_node = u
        if v > max_node:
            max_node = v

    q = int(next(it))
    queries = []
    for i in range(q):
        t = int(next(it))
        queries.append((t, i))

    # Deterministic indexing detection:
    # 1-indexed iff every node id is in [1, n] and at least one equals n,
    # and no node id equals 0.
    one_indexed = False
    if m > 0 and n > 0:
        if min_node >= 1 and max_node <= n and max_node == n:
            one_indexed = True
        elif min_node == 0 and max_node <= n - 1:
            one_indexed = False
        else:
            # Fallback: if any id equals n, assume 1-indexed
            one_indexed = (max_node == n)

    shift = 1 if one_indexed else 0
    edges = []
    for w, u, v in raw_edges:
        edges.append((w, u - shift, v - shift))

    edges.sort(key=lambda e: e[0])
    queries.sort(key=lambda x: x[0])

    dsu = DSU(n)
    components = n
    largest = 0 if n == 0 else 1

    ans_components = [0] * q
    ans_largest = [0] * q

    ei = 0
    for t, idx in queries:
        while ei < m and edges[ei][0] <= t:
            _, u, v = edges[ei]
            merged, new_size = dsu.union(u, v)
            if merged:
                components -= 1
                if new_size > largest:
                    largest = new_size
            ei += 1
        ans_components[idx] = components
        ans_largest[idx] = largest

    out = []
    for i in range(q):
        out.append(f"{ans_components[i]} {ans_largest[i]}")
    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    solve()