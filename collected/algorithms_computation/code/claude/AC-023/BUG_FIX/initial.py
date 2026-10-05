from typing import List, Tuple


def components_by_threshold(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
) -> List[Tuple[int, int]]:
    """For each q, return (number_of_components, largest_component_size)
    using only edges with weight <= q. Deterministic, stdlib only."""
    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:          # path compression (iterative)
            parent[x], x = root, parent[x]
        return root

    sorted_edges = sorted(edges, key=lambda e: e[2])
    order = sorted(range(len(queries)), key=lambda i: queries[i])

    comps = n
    largest = 1 if n > 0 else 0
    ei = 0
    m = len(sorted_edges)
    answers: List[Tuple[int, int]] = [(0, 0)] * len(queries)

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
                comps -= 1
                if size[ru] > largest:
                    largest = size[ru]
        answers[qi] = (comps, largest)

    return answers


if __name__ == "__main__":
    n = 5
    edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5)]
    queries = [0, 1, 2, 3, 5]
    print(components_by_threshold(n, edges, queries))
    # [(5, 1), (4, 2), (3, 2), (2, 3), (1, 5)]