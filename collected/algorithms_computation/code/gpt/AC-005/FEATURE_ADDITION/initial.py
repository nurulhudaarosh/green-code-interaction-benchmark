from typing import List


def longest_increasing_subsequence_indices(a: List[int]) -> List[int]:
    """
    Return the lexicographically smallest original-index sequence among
    all maximum-length strictly increasing subsequences.

    Indices are 0-based.

    Time:  O(n^2)
    Space: O(n^2) in the worst case due to explicit index sequences.
    """
    n = len(a)

    if n == 0:
        return []

    # length[i] = best LIS length ending at i.
    length = [1] * n

    # predecessor[i] = predecessor index chosen for i.
    predecessor = [None] * n

    # sequence[i] = lexicographically smallest index sequence for
    # a best increasing subsequence ending at i.
    sequence = [[i] for i in range(n)]

    for i in range(n):
        for j in range(i):
            # Strictly increasing requirement.
            if a[j] >= a[i]:
                continue

            candidate_length = length[j] + 1
            candidate_sequence = sequence[j] + [i]

            if candidate_length > length[i]:
                length[i] = candidate_length
                predecessor[i] = j
                sequence[i] = candidate_sequence

            elif candidate_length == length[i]:
                # Explicit lexicographic tie breaking.
                if candidate_sequence < sequence[i]:
                    predecessor[i] = j
                    sequence[i] = candidate_sequence

    # Find the globally optimal length.
    best_length = max(length)

    # Among all globally optimal subsequences, choose the
    # lexicographically smallest original-index sequence.
    best_sequence = None

    for i in range(n):
        if length[i] == best_length:
            if best_sequence is None or sequence[i] < best_sequence:
                best_sequence = sequence[i]

    # best_sequence cannot be None because n > 0.
    return best_sequence