import sys
from typing import List, Tuple, Optional


class DSU:
    __slots__ = ("parent", "size", "num_components", "max_size")

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.num_components = n
        self.max_size = 1 if n > 0 else 0

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:          # path compression
            nxt = self.parent[x]
            self.parent[x] = root
            x = nxt
        return root

    def union(self, a: int, b: int) -> bool:
        """Attempt a union; return True if a merge happened."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:      # union by size
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.num_components -= 1
        if self.size[ra] > self.max_size:
            self.max_size = self.size[ra]
        return True


def solve(n: int,
          edges: List[Tuple[int, int, int]],
          queries: List[int],
          with_summary: bool = False):
    """
    Returns the original results. If with_summary is True, each result gains
    an 'operation_summary' dict and a top-level summary is also returned.
    Original 2 fields remain unchanged and in place.
    """
    if n == 0:
        results = [[0, 0] for _ in queries]
        if with_summary:
            empty = {
                "edges_processed": 0, "union_attempts": 0,
                "unions_succeeded": 0, "unions_skipped": 0,
                "queries_finalized": 0, "total_major_operations": 0,
            }
            results = [[c, s, dict(empty)] for c, s in results]
            return results, dict(empty)
        return results

    edges_sorted = sorted(edges, key=lambda e: e[2])
    indexed_queries = sorted(enumerate(queries), key=lambda x: x[1])

    dsu = DSU(n)
    results: List[list] = [None] * len(queries)

    # Deterministic counters
    edges_processed = 0
    union_attempts = 0
    unions_succeeded = 0
    unions_skipped = 0
    queries_finalized = 0

    ei, m = 0, len(edges_sorted)

    for orig_idx, q in indexed_queries:
        # Add every edge with weight <= q
        while ei < m and edges_sorted[ei][2] <= q:
            u, v, _ = edges_sorted[ei]
            edges_processed += 1                     # major op: edge-scan step
            union_attempts += 1                      # major op: union attempt
            if dsu.union(u, v):
                unions_succeeded += 1
            else:
                unions_skipped += 1
            ei += 1

        queries_finalized += 1                       # major op: query finalized

        base = [dsu.num_components, dsu.max_size]    # ORIGINAL fields, unchanged
        if with_summary:
            running = {
                "edges_processed": edges_processed,
                "union_attempts": union_attempts,
                "unions_succeeded": unions_succeeded,
                "unions_skipped": unions_skipped,
                "queries_finalized": queries_finalized,
                "total_major_operations": (
                    edges_processed + union_attempts + queries_finalized
                ),
            }
            results[orig_idx] = base + [running]
        else:
            results[orig_idx] = base                 # exactly original shape

    if with_summary:
        top = {
            "edges_processed": edges_processed,
            "union_attempts": union_attempts,
            "unions_succeeded": unions_succeeded,
            "unions_skipped": unions_skipped,
            "queries_finalized": queries_finalized,
            "total_major_operations": (
                edges_processed + union_attempts + queries_finalized
            ),
        }
        return results, top

    return results


def _parse(data: List[str]):
    pos = 0
    n = int(data[pos]); pos += 1
    m = int(data[pos]); pos += 1
    edges = []
    for _ in range(m):
        u = int(data[pos]); v = int(data[pos + 1]); w = int(data[pos + 2])
        pos += 3
        edges.append((u, v, w))
    qn = int(data[pos]); pos += 1
    queries = [int(data[pos + i]) for i in range(qn)]
    return n, edges, queries


def main():
    data = sys.stdin.read().split()
    if not data:
        return

    # Feature toggle: presence of '--summary' on argv enables the new field.
    with_summary = "--summary" in sys.argv[1:]

    n, edges, queries = _parse(data)

    if with_summary:
        results, top = solve(n, edges, queries, with_summary=True)
        # Preserve original fields exactly, add only the extra field.
        out_lines = []
        for comp, mx, summary in results:
            out_lines.append(f"{comp} {mx} {summary}")
        out_lines.append(f"operation_summary {top}")
        sys.stdout.write("\n".join(out_lines) + "\n")
    else:
        results = solve(n, edges, queries, with_summary=False)
        out_lines = [f"{comp} {mx}" for comp, mx in results]
        sys.stdout.write("\n".join(out_lines) + "\n")


if __name__ == "__main__":
    main()