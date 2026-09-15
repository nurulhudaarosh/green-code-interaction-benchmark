from typing import Sequence, Tuple


def longest_increasing_subsequence(
    a: Sequence[int],
) -> Tuple[int, list[int]]:
    """
    Find a maximum-length strictly increasing subsequence.

    Tie-breaking:
        Among all maximum-length subsequences, return the one whose
        original-index sequence is lexicographically smallest.

    Indices are 0-based.

    Returns:
        (maximum_length, index_sequence)
    """
    n = len(a)

    if n == 0:
        return 0, []

    # dp[i] = lexicographically smallest index sequence among the
    # longest strictly increasing subsequences ending at i.
    dp: list[tuple[int, ...]] = [() for _ in range(n)]

    for i in range(n):
        # Every single element forms a valid subsequence.
        best = (i,)

        for j in range(i):
            if a[j] < a[i]:
                candidate = dp[j] + (i,)

                # Prefer longer subsequences. For equal lengths,
                # explicitly apply lexicographic tie-breaking.
                if (
                    len(candidate) > len(best)
                    or (
                        len(candidate) == len(best)
                        and candidate < best
                    )
                ):
                    best = candidate

        dp[i] = best

    # Select the globally optimal subsequence.
    answer = dp[0]

    for i in range(1, n):
        candidate = dp[i]

        if (
            len(candidate) > len(answer)
            or (
                len(candidate) == len(answer)
                and candidate < answer
            )
        ):
            answer = candidate

    return len(answer), list(answer)


if __name__ == "__main__":
    tests = [
        [],
        [5],
        [1, 2, 3, 4],
        [4, 3, 2, 1],
        [3, 1, 2, 2, 4],
        [2, 1, 3, 2, 4],
        [1, 1, 1],
    ]

    for sequence in tests:
        length, indices = longest_increasing_subsequence(sequence)
        values = [sequence[i] for i in indices]

        print(
            f"a={sequence} "
            f"-> length={length}, indices={indices}, values={values}"
        )