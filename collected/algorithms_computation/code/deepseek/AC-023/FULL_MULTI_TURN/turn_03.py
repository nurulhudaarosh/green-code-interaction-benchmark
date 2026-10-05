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


def solve(emit_operation_summary=False):
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

    # Deterministic indexing detection (1-indexed vs 0-indexed)
    one_indexed = False
    if m > 0 and n > 0:
        if min_node >= 1 and max_node <= n and max_node == n:
            one_indexed = True
        elif min_node == 0 and max_node <= n - 1:
            one_indexed = False
        else:
            one_indexed = (max_node == n)

    shift = 1 if one_indexed else 0
    edges = [(w, u - shift, v - shift) for (w, u, v) in raw_edges]

    edges.sort(key=lambda e: e[0])
    queries.sort(key=lambda x: x[0])

    dsu = DSU(n)
    components = n
    largest = 0 if n == 0 else 1

    ans_components = [0] * q
    ans_largest = [0] * q

    # Operation counters (deterministic)
    edge_union_attempts = 0
    successful_unions = 0
    largest_updates = 0
    query_resolutions = 0

    ei = 0
    for t, idx in queries:
        while ei < m and edges[ei][0] <= t:
            _, u, v = edges[ei]
            edge_union_attempts += 1
            merged, new_size = dsu.union(u, v)
            if merged:
                successful_unions += 1
                components -= 1
                if new_size > largest:
                    largest = new_size
                    largest_updates += 1
            ei += 1
        ans_components[idx] = components
        ans_largest[idx] = largest
        query_resolutions += 1

    out_lines = []
    for i in range(q):
        out_lines.append(f"{ans_components[i]} {ans_largest[i]}")

    if emit_operation_summary:
        total_major_operations = (
            edge_union_attempts + largest_updates + query_resolutions
        )
        out_lines.append(
            "operation_summary "
            f"edge_union_attempts={edge_union_attempts} "
            f"successful_unions={successful_unions} "
            f"largest_updates={largest_updates} "
            f"query_resolutions={query_resolutions} "
            f"total_major_operations={total_major_operations}"
        )

    sys.stdout.write("\n".join(out_lines))


if __name__ == "__main__":
    # Feature toggle: set True to emit operation_summary, False for legacy behavior.
    emit = "--operation-summary" in sys.argv[1:]
    solve(emit_operation_summary=emit)