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

Algorithm:
    Dynamic programming with an explicit adjacent-transposition transition.

Requirements:
    - Deterministic
    - Standard library only
    - No network/API/external services/randomness
"""


def edit_distance_with_transposition(source: str, target: str) -> int:
    """
    Compute the minimum edit distance between source and target using:

        - insertion
        - deletion
        - substitution
        - adjacent transposition

    Each operation costs 1.

    Returns:
        The minimum edit distance as an integer.
    """

    n = len(source)
    m = len(target)

    # dp[i][j] = minimum cost to transform
    # source[:i] into target[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases:
    # Transforming a prefix into an empty string requires deletions.
    for i in range(1, n + 1):
        dp[i][0] = i

    # Transforming an empty string into a prefix requires insertions.
    for j in range(1, m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):

            # 1. Insertion
            insertion = dp[i][j - 1] + 1

            # 2. Deletion
            deletion = dp[i - 1][j] + 1

            # 3. Match or substitution
            substitution = dp[i - 1][j - 1] + (
                0 if source[i - 1] == target[j - 1] else 1
            )

            # Fixed candidate ordering makes tie handling deterministic.
            best = min(insertion, deletion, substitution)

            # 4. Explicit adjacent transposition
            #
            # Example:
            #     source: ...ab
            #     target: ...ba
            #
            # We can transform ...ab -> ...ba using one transposition.
            if (
                i >= 2
                and j >= 2
                and source[i - 2] == target[j - 1]
                and source[i - 1] == target[j - 2]
            ):
                transposition = dp[i - 2][j - 2] + 1
                best = min(best, transposition)

            dp[i][j] = best

    return dp[n][m]


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def run_tests() -> None:
    # Identical strings
    assert edit_distance_with_transposition("abc", "abc") == 0

    # Empty strings
    assert edit_distance_with_transposition("", "") == 0
    assert edit_distance_with_transposition("", "abc") == 3
    assert edit_distance_with_transposition("abc", "") == 3

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
    assert edit_distance_with_transposition("abba", "baab") == 2

    # Single-character strings
    assert edit_distance_with_transposition("a", "a") == 0
    assert edit_distance_with_transposition("a", "b") == 1

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()

    # Example
    source = "abcd"
    target = "acbd"

    distance = edit_distance_with_transposition(source, target)

    print(f"Source: {source}")
    print(f"Target: {target}")
    print(f"Edit distance: {distance}")