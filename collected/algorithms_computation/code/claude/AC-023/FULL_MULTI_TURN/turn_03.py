from typing import Dict, List, Tuple, Union

Answer = Tuple[int, int]


def component_stats(
    n: int,
    edges: List[Tuple[int, int, int]],
    queries: List[int],
    include_summary: bool = False,
) -> Union[List[Answer], Dict[str, object]]:
    """For each q in queries, return (num_components, largest_component_size)
    using only edges with weight <= q. Vertices are 0..n-1.

    include_summary=False -> list of (components, largest) pairs (original output).
    include_summary=True  -> {"answers": [...], "operation_summary": {...}}.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    for u, v, _ in edges:
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"edge endpoint out of range: ({u}, {v}) for n={n}")

    parent = list(range(n))
    size = [1] * n
    components = n
    largest = 1 if n > 0 else 0

    find_calls = 0
    unions_performed = 0
    redundant_skipped = 0

    def find(x: int) -> int:
        nonlocal find_calls
        find_calls += 1
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:              # path compression
            parent[x], x = root, parent[x]
        return root

    sorted_edges = sorted(edges, key=lambda e: e[2])        # stable on ties
    order = sorted(range(len(queries)), key=lambda i: (queries[i], i))
    answers: List[Answer] = [(0, 0)] * len(queries)

    ptr, m = 0, len(sorted_edges)
    for qi in order:
        q = queries[qi]
        while ptr < m and sorted_edges[ptr][2] <= q:
            u, v, _ = sorted_edges[ptr]
            ptr += 1
            ru, rv = find(u), find(v)
            if ru == rv:
                redundant_skipped += 1
                continue
            if size[ru] < size[rv]:           # union by size
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
            components -= 1
            unions_performed += 1
            if size[ru] > largest:
                largest = size[ru]
        answers[qi] = (components, largest)

    if not include_summary:
        return answers

    return {
        "answers": answers,
        "operation_summary": {
            "edges_sorted": m,
            "queries_sorted": len(queries),
            "edges_processed": ptr,
            "unions_performed": unions_performed,
            "redundant_edges_skipped": redundant_skipped,
            "find_calls": find_calls,
            "queries_answered": len(queries),
            "total_major_operations": ptr + len(queries),
        },
    }


if __name__ == "__main__":
    n = 4
    edges = [(0, 1, 2), (1, 2, 2), (2, 3, 4)]
    queries = [2, 2, 1, 4]

    # Feature off: identical to the original output.
    print(component_stats(n, edges, queries))
    # [(2, 3), (2, 3), (4, 1), (1, 4)]

    # Feature on.
    print(component_stats(n, edges, queries, include_summary=True))
    # {'answers': [(2, 3), (2, 3), (4, 1), (1, 4)],
    #  'operation_summary': {'edges_sorted': 3, 'queries_sorted': 4,
    #   'edges_processed': 3, 'unions_performed': 3,
    #   'redundant_edges_skipped': 0, 'find_calls': 6,
    #   'queries_answered': 4, 'total_major_operations': 7}}

    # Redundant edge example: the triangle's third edge is skipped.
    print(component_stats(3, [(0, 1, 1), (1, 2, 1), (0, 2, 1)], [1],
                          include_summary=True)["operation_summary"])
    # edges_processed=3, unions_performed=2, redundant_edges_skipped=1