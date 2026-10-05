from typing import Dict, List, Tuple, Union


def components_by_threshold(
    n: int,
    edges: List[Tuple[int, int, float]],
    queries: List[float],
    include_summary: bool = False,
) -> Union[List[Tuple[int, int]], Dict[str, object]]:
    """For each q, using only edges with weight <= q, return
    (number_of_components, largest_component_size).

    If include_summary is False (default), returns the original list.
    If True, returns {"answers": [...], "operation_summary": {...}}.
    """
    parent = list(range(n))
    size = [1] * n

    find_calls = 0
    rewrites = 0
    merges = 0
    redundant = 0

    def find(x: int) -> int:
        nonlocal find_calls, rewrites
        find_calls += 1
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:          # path compression
            parent[x], x = root, parent[x]
            rewrites += 1
        return root

    comps = n
    largest = 1 if n > 0 else 0

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
                comps -= 1
                merges += 1
                if size[ru] > largest:
                    largest = size[ru]
            else:
                redundant += 1
        answers[qi] = (comps, largest)

    if not include_summary:
        return answers

    summary = {
        "edges_sorted": m,
        "queries_sorted": len(queries),
        "edges_processed": ei,
        "find_calls": find_calls,
        "successful_merges": merges,
        "redundant_edges": redundant,
        "path_compression_rewrites": rewrites,
        "queries_answered": len(queries),
    }
    summary["total_major_operations"] = (
        m + len(queries) + find_calls + merges + redundant + rewrites + len(queries)
    )
    return {"answers": answers, "operation_summary": summary}


if __name__ == "__main__":
    edges = [(0, 1, 1), (1, 2, 3), (3, 4, 2), (2, 3, 5)]
    queries = [0, 1, 2, 3, 5, 4]

    print(components_by_threshold(5, edges, queries))
    # [(5, 1), (4, 2), (3, 2), (2, 3), (1, 5), (2, 3)]

    print(components_by_threshold(5, edges, queries, include_summary=True))
    # {'answers': [(5, 1), (4, 2), (3, 2), (2, 3), (1, 5), (2, 3)],
    #  'operation_summary': {'edges_sorted': 4, 'queries_sorted': 6,
    #   'edges_processed': 4, 'find_calls': 8, 'successful_merges': 4,
    #   'redundant_edges': 0, 'path_compression_rewrites': 0,
    #   'queries_answered': 6, 'total_major_operations': 28}}