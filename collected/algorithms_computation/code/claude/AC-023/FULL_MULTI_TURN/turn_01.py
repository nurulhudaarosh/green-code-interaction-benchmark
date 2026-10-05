from typing import List, Tuple


def component_stats(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
) -> List[Tuple[int, int]]:
    """For each q in queries, return (num_components, largest_component_size)
    using only edges with weight <= q. Vertices are 0..n-1."""
    parent = list(range(n))
    size = [1] * n
    components = n
    largest = 1 if n > 0 else 0

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:          # path compression
            parent[x], x = root, parent[x]
        return root

    sorted_edges = sorted(edges, key=lambda e: e[2])
    order = sorted(range(len(queries)), key=lambda i: (queries[i], i))
    answers: List[Tuple[int, int]] = [(0, 0)] * len(queries)

    ptr = 0
    m = len(sorted_edges)
    for qi in order:
        q = queries[qi]
        while ptr < m and sorted_edges[ptr][2] <= q:
            u, v, _ = sorted_edges[ptr]
            ptr += 1
            ru, rv = find(u), find(v)
            if ru == rv:
                continue
            if size[ru] < size[rv]:       # union by size
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
            components -= 1
            if size[ru] > largest:
                largest = size[ru]
        answers[qi] = (components, largest)

    return answers


if __name__ == "__main__":
    n = 5
    edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5)]
    queries = [3, 0, 5, 1, 2]
    print(component_stats(n, edges, queries))
    # [(2, 3), (5, 1), (1, 5), (4, 2), (3, 2)]