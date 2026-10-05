def component_stats(n, edges, queries):
    """
    n       : number of vertices (labelled 0..n-1)
    edges   : iterable of (u, v, w)
    queries : list of thresholds q
    returns : list of (num_components, largest_component_size) per query
    """
    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:          # path compression
            parent[x], x = root, parent[x]
        return root

    sorted_edges = sorted(edges, key=lambda e: e[2])
    order = sorted(range(len(queries)), key=lambda i: queries[i])

    components = n
    largest = 1 if n > 0 else 0
    ptr = 0
    m = len(sorted_edges)
    answers = [None] * len(queries)

    for qi in order:
        q = queries[qi]
        while ptr < m and sorted_edges[ptr][2] <= q:
            u, v, _ = sorted_edges[ptr]
            ptr += 1
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
    n = 5
    edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5)]
    queries = [3, 0, 10, 1, 5, 2]
    print(component_stats(n, edges, queries))
    # [(2, 3), (5, 1), (1, 5), (4, 2), (1, 5), (3, 2)]