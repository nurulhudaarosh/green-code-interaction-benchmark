from typing import Sequence, List, Dict, Any


def longest_increasing_route(a: Sequence[int]) -> Dict[str, Any]:
    """
    Find a longest strictly increasing subsequence.

    Among all longest subsequences, return the one whose sequence
    of original indices is lexicographically smallest.

    Uses O(n^2) dynamic programming with explicit predecessor/index-
    sequence tie breaking.
    """
    n = len(a)

    if n == 0:
        return {
            "length": 0,
            "values": [],
            "indices": [],
        }

    # dp_len[i] is the maximum length of a strictly increasing
    # subsequence ending at index i.
    dp_len = [1] * n

    # predecessor[i] stores the selected predecessor index.
    predecessor = [None] * n

    # index_seq[i] stores the lexicographically smallest original-index
    # sequence among all optimal subsequences ending at i.
    index_seq: List[List[int]] = [[i] for i in range(n)]

    # Quadratic dynamic programming.
    for i in range(n):
        for j in range(i):
            if a[j] < a[i]:
                candidate_len = dp_len[j] + 1

                if candidate_len > dp_len[i]:
                    dp_len[i] = candidate_len
                    predecessor[i] = j
                    index_seq[i] = index_seq[j] + [i]

                elif candidate_len == dp_len[i]:
                    candidate_indices = index_seq[j] + [i]

                    # Explicit lexicographic tie-breaking.
                    if candidate_indices < index_seq[i]:
                        predecessor[i] = j
                        index_seq[i] = candidate_indices

    # Select the globally optimal subsequence:
    # 1. Maximum length.
    # 2. Lexicographically smallest original-index sequence.
    best_i = 0

    for i in range(1, n):
        if dp_len[i] > dp_len[best_i]:
            best_i = i
        elif dp_len[i] == dp_len[best_i]:
            if index_seq[i] < index_seq[best_i]:
                best_i = i

    best_indices = index_seq[best_i]
    best_values = [a[i] for i in best_indices]

    return {
        "length": dp_len[best_i],
        "values": best_values,
        "indices": best_indices,
    }


if __name__ == "__main__":
    sequence = [3, 4, 1, 2, 5]

    result = longest_increasing_route(sequence)

    print(result)