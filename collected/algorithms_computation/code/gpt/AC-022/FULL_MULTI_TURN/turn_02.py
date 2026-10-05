"""
Edit Distance With Adjacent Transposition

Problem:
    Given two strings, compute the minimum number of unit-cost operations
    required to transform source into target.

Allowed operations:
    1. Insertion
    2. Deletion
    3. Substitution
    4. Adjacent transposition

Each operation costs 1.

Requirements:
    - Dynamic programming
    - Explicit adjacent-transposition transition
    - Deterministic tie handling
    - Correct handling of repeated characters and empty strings
    - Return exactly the edit distance
    - Standard library only
"""


def edit_distance_with_transposition(source: str, target: str) -> int:
    """
    Return the minimum edit distance between source and target.

    Deterministic tie-breaking priority:
        1. Match/substitution
        2. Transposition
        3. Insertion
        4. Deletion

    Only the minimum distance is returned.
    """

    n = len(source)
    m = len(target)

    # dp[i][j] = minimum cost to transform
    # source[:i] into target[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Fixed priorities for deterministic tie handling.
    SUBSTITUTION = 0
    TRANSPOSITION = 1
    INSERTION = 2
    DELETION = 3

    # Base cases.
    for i in range(1, n + 1):
        dp[i][0] = i

    for j in range(1, m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):

            candidates = []

            # 1. Match / substitution
            substitution_cost = (
                0 if source[i - 1] == target[j - 1] else 1
            )

            candidates.append(
                (
                    dp[i - 1][j - 1] + substitution_cost,
                    SUBSTITUTION
                )
            )

            # 2. Explicit adjacent transposition
            #
            # Example:
            #     source: ...ab
            #     target: ...ba
            #
            # The final two characters can be swapped in one operation.
            if (
                i >= 2
                and j >= 2
                and source[i - 2] == target[j - 1]
                and source[i - 1] == target[j - 2]
            ):
                candidates.append(
                    (
                        dp[i - 2][j - 2] + 1,
                        TRANSPOSITION
                    )
                )

            # 3. Insertion
            candidates.append(
                (
                    dp[i][j - 1] + 1,
                    INSERTION
                )
            )

            # 4. Deletion
            candidates.append(
                (
                    dp[i - 1][j] + 1,
                    DELETION
                )
            )

            # Compare first by cost, then by fixed priority.
            # This makes equal-cost decisions deterministic.
            dp[i][j] = min(candidates)[0]

    return dp[n][m]


def run_tests() -> None:
    # Empty strings
    assert edit_distance_with_transposition("", "") == 0
    assert edit_distance_with_transposition("", "abc") == 3
    assert edit_distance_with_transposition("abc", "") == 3

    # Identical strings
    assert edit_distance_with_transposition("abc", "abc") == 0

    # Insertion
    assert edit_distance_with_transposition("abc", "abcd") == 1

    # Deletion
    assert edit_distance_with_transposition("abcd", "abc") == 1

    # Substitution
    assert edit_distance_with_transposition("cat", "cut") == 1

    # Adjacent transposition
    assert edit_distance_with_transposition("ab", "ba") == 1

    # Transposition inside a longer string
    assert edit_distance_with_transposition("abcd", "acbd") == 1

    # Multiple operations
    assert edit_distance_with_transposition("kitten", "sitting") == 3

    # Repeated characters
    assert edit_distance_with_transposition("aab", "aba") == 1
    assert edit_distance_with_transposition("aba", "aab") == 1
    assert edit_distance_with_transposition("abba", "baab") == 2

    # Small valid deterministic-tie example
    assert edit_distance_with_transposition("ab", "bc") == 2

    # Single-character cases
    assert edit_distance_with_transposition("a", "a") == 0
    assert edit_distance_with_transposition("a", "b") == 1

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()

    source = "abcd"
    target = "acbd"

    result = edit_distance_with_transposition(source, target)

    print("Source:", source)
    print("Target:", target)
    print("Edit distance:", result)