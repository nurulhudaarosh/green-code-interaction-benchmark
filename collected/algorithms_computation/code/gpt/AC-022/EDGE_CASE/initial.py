def edit_distance_with_transposition(source: str, target: str) -> int:
    """
    Compute the edit distance between two strings using:
      - insertion: 1
      - deletion: 1
      - substitution: 1
      - adjacent transposition: 1

    Uses dynamic programming with an explicit transposition transition.

    Returns:
        int: Minimum edit distance.
    """

    n = len(source)
    m = len(target)

    # dp[i][j] = minimum cost to transform
    # source[:i] into target[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases
    for i in range(n + 1):
        dp[i][0] = i

    for j in range(m + 1):
        dp[0][j] = j

    # Fill the DP table
    for i in range(1, n + 1):
        for j in range(1, m + 1):

            # 1. Substitution / match
            substitution_cost = 0 if source[i - 1] == target[j - 1] else 1
            substitution = dp[i - 1][j - 1] + substitution_cost

            # 2. Deletion
            deletion = dp[i - 1][j] + 1

            # 3. Insertion
            insertion = dp[i][j - 1] + 1

            # Fixed deterministic candidate order:
            # substitution, deletion, insertion
            candidates = [
                substitution,
                deletion,
                insertion,
            ]

            # 4. Explicit adjacent transposition transition
            if (
                i >= 2
                and j >= 2
                and source[i - 1] == target[j - 2]
                and source[i - 2] == target[j - 1]
            ):
                transposition = dp[i - 2][j - 2] + 1
                candidates.append(transposition)

            dp[i][j] = min(candidates)

    return dp[n][m]


# -------------------------
# Tests
# -------------------------

assert edit_distance_with_transposition("", "") == 0
assert edit_distance_with_transposition("", "abc") == 3
assert edit_distance_with_transposition("abc", "") == 3

# Matching strings
assert edit_distance_with_transposition("abc", "abc") == 0

# Substitution
assert edit_distance_with_transposition("cat", "cut") == 1

# Insertion
assert edit_distance_with_transposition("cat", "cart") == 1

# Deletion
assert edit_distance_with_transposition("cart", "cat") == 1

# Adjacent transposition
assert edit_distance_with_transposition("ab", "ba") == 1

# More examples
assert edit_distance_with_transposition("ca", "abc") == 2
assert edit_distance_with_transposition("abcdef", "abcfde") == 2

print(edit_distance_with_transposition("kitten", "sitting"))
print(edit_distance_with_transposition("ab", "ba"))