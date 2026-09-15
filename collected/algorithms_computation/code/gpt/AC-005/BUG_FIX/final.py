from typing import Sequence


def longest_increasing_route(
    sequence: Sequence[int],
) -> tuple[int, list[int]]:
    """
    Return the maximum length strictly increasing subsequence and,
    among all optimal subsequences, the lexicographically smallest
    sequence of original 0-based indices.

    Uses quadratic dynamic programming with explicit
    index-sequence tie breaking.
    """
    n = len(sequence)

    if n == 0:
        return 0, []

    # dp[i] is the lexicographically smallest index sequence among
    # all longest strictly increasing subsequences ending at i.
    dp: list[tuple[int, ...]] = [() for _ in range(n)]

    for i in range(n):
        # A subsequence containing only sequence[i].
        best = (i,)

        for j in range(i):
            # Strictly increasing requirement.
            if sequence[j] < sequence[i]:
                candidate = dp[j] + (i,)

                # Primary criterion: maximum length.
                # Secondary criterion: lexicographically smallest
                # original-index sequence.
                if len(candidate) > len(best):
                    best = candidate
                elif (
                    len(candidate) == len(best)
                    and candidate < best
                ):
                    best = candidate

        dp[i] = best

    # Select the best subsequence globally.
    answer = dp[0]

    for i in range(1, n):
        candidate = dp[i]

        if len(candidate) > len(answer):
            answer = candidate
        elif (
            len(candidate) == len(answer)
            and candidate < answer
        ):
            answer = candidate

    return len(answer), list(answer)


# Small regression tests
def _run_tests() -> None:
    assert longest_increasing_route([]) == (0, [])

    assert longest_increasing_route([5]) == (1, [0])

    assert longest_increasing_route(
        [1, 2, 3, 4]
    ) == (4, [0, 1, 2, 3])

    assert longest_increasing_route(
        [4, 3, 2, 1]
    ) == (1, [0])

    # Important tie-breaking case.
    assert longest_increasing_route(
        [1, 2, 1, 2, 3]
    ) == (3, [0, 1, 4])

    # Duplicate values cannot both be selected because the
    # subsequence must be strictly increasing.
    assert longest_increasing_route(
        [1, 1, 1]
    ) == (1, [0])

    assert longest_increasing_route(
        [3, 1, 2, 2, 4]
    ) == (3, [1, 2, 4])


if __name__ == "__main__":
    _run_tests()
    print("All tests passed.")