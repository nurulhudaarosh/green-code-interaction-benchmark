from typing import List, Tuple, Sequence


def components_by_threshold(
    n: int,
    edges: Sequence[Tuple[int, int, float]],
    queries: Sequence[float],
) -> List[Tuple[int, int]]:
    """
    n       : number of vertices (labeled 0..n-1)
    edges   : iterable of (u, v, w)
    queries : thresholds q; for each, use only edges with w <= q
    returns : list of (num_components, largest_component_size) per query,
              in the original query order.
    """
    parent = list(range(n))
    size = [1] * n
    components = n
    largest = 1 if n > 0 else 0

    def find(x: int) -> int:
        # Iterative find with path compression.
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    sorted_edges = sorted(edges, key=lambda e: e[2])
    order = sorted(range(len(queries)), key=lambda i: queries[i])

    answers: List[Tuple[int, int]] = [(0, 0)] * len(queries)
    ei = 0
    m = len(sorted_edges)

    for qi in order:
        q = queries[qi]
        while ei < m and sorted_edges[ei][2] <= q:
            u, v, _ = sorted_edges[ei]
            ei += 1
            ru, rv = find(u), find(v)
            if ru != rv:
                if size[ru] < size[rv]:
                    ru, rv = rv, ru
                parent[rv] = ru
                size[ru] += size[rv]
                components -= 1
                if size[ru] > largest:
                    largest = size[ru]
        answers[qi] = (components, largest)

    return answers


if __name__ == "__main__":
    n = 6
    edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5), (4, 5, 7)]
    queries = [0, 1, 2, 3, 5, 7, 4]
    result = components_by_threshold(n, edges, queries)
    for q, (c, L) in zip(queries, result):
        print(f"q={q}: components={c}, largest={L}")