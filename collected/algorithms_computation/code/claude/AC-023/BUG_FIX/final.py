from typing import List, Tuple


def components_by_threshold(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
) -> List[Tuple[int, int]]:
    """For each q, return (number_of_components, largest_component_size)
    using only edges with weight <= q. Deterministic, stdlib only."""
    if n < 0:
        raise ValueError("n must be non-negative")
    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"edge endpoint out of range: {(u, v)}")

    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    # Total order: ties on weight broken by (u, v), so processing is deterministic.
    sorted_edges = sorted(edges, key=lambda e: (e[2], e[0], e[1]))
    order = sorted(range(len(queries)), key=lambda i: (queries[i], i))

    comps = n
    largest = 1 if n > 0 else 0
    ei, m = 0, len(sorted_edges)
    answers: List[Tuple[int, int]] = [(0, 0)] * len(queries)

    for qi in order:
        q = queries[qi]
        while ei < m and sorted_edges[ei][2] <= q:
            u, v, _ = sorted_edges[ei]
            ei += 1
            ru, rv = find(u), find(v)
            if ru != rv:
                if size[ru] < size[rv] or (size[ru] == size[rv] and ru > rv):
                    ru, rv = rv, ru
                parent[rv] = ru
                size[ru] += size[rv]
                comps -= 1
                if size[ru] > largest:
                    largest = size[ru]
        answers[qi] = (comps, largest)

    return answers


def _brute(n, edges, q):
    """Reference: rebuild components from scratch for one threshold."""
    adj = {i: set() for i in range(n)}
    for u, v, w in edges:
        if w <= q:
            adj[u].add(v)
            adj[v].add(u)
    seen, sizes = set(), []
    for s in range(n):
        if s in seen:
            continue
        stack, cnt = [s], 0
        seen.add(s)
        while stack:
            x = stack.pop()
            cnt += 1
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        sizes.append(cnt)
    return (len(sizes), max(sizes, default=0))


if __name__ == "__main__":
    edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5)]
    qs = [5, 0, 3, 3, 1, 2]
    got = components_by_threshold(5, edges, qs)
    assert got == [_brute(5, edges, q) for q in qs]
    print(got)  # [(1, 5), (5, 1), (2, 3), (2, 3), (4, 2), (3, 2)]

    try:
        components_by_threshold(3, [(-1, 0, 1)], [1])
    except ValueError as e:
        print("rejected:", e)