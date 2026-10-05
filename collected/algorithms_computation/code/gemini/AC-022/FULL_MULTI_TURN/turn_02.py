def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the true Damerau-Levenshtein edit distance between s1 and s2

    allowing insertions, deletions, substitutions, and adjacent transpositions,
    each with cost 1.
    """
    n, m = len(s1), len(s2)

    # Upper bound to initialize padding cells
    max_dist = n + m

    # Unique alphabet present across both strings
    alphabet = set(s1) | set(s2)

    # da stores the last row index in s1 where character ch appeared
    da = {ch: 0 for ch in alphabet}

    # dp table has dimension (n + 2) x (m + 2) to accommodate 1-based indexing
    # with an extra boundary row/column at index 0
    dp = [[0] * (m + 2) for _ in range(n + 2)]

    dp[0][0] = max_dist
    for i in range(0, n + 1):
        dp[i + 1][0] = max_dist
        dp[i + 1][1] = i
    for j in range(0, m + 1):
        dp[0][j + 1] = max_dist
        dp[1][j + 1] = j

    for i in range(1, n + 1):
        db = 0  # Last column index in s2 where s1[i-1] was observed
        for j in range(1, m + 1):
            k = da[s2[j - 1]]
            l = db

            if s1[i - 1] == s2[j - 1]:
                cost = 0
                db = j
            else:
                cost = 1

            # Standard operations: deletion, insertion, substitution
            del_cost = dp[i][j + 1] + 1
            ins_cost = dp[i + 1][j] + 1
            sub_cost = dp[i][j] + cost

            dp[i + 1][j + 1] = min(del_cost, ins_cost, sub_cost)

            # Explicit transposition transition (generalized across insertions/deletions)
            if k > 0 and l > 0:
                trans_cost = (
                    dp[k][l]  # Subproblem before transposition
                    + (i - k - 1)  # Intervening deletions
                    + (j - l - 1)  # Intervening insertions
                    + 1  # Transposition cost
                )
                dp[i + 1][j + 1] = min(dp[i + 1][j + 1], trans_cost)

        da[s1[i - 1]] = i

    return dp[n + 1][m + 1]


if __name__ == "__main__":
    # Small valid example demonstrating the fix
    # "CA" -> "AC" (transposition, 1) -> "ABC" (insertion of 'B', 1) => 2
    assert damerau_levenshtein_distance("CA", "ABC") == 2

    # Standard operations verification
    assert damerau_levenshtein_distance("cat", "cat") == 0
    assert damerau_levenshtein_distance("cat", "cats") == 1
    assert damerau_levenshtein_distance("cat", "at") == 1
    assert damerau_levenshtein_distance("cat", "bat") == 1
    assert damerau_levenshtein_distance("ca", "ac") == 1