from typing import Tuple


def lcs(x: str, y: str) -> Tuple[int, str]:
    """
    Return (LCS length, one deterministic LCS).

    Tie-breaking rule:
    If dp[i-1][j] == dp[i][j-1], prefer advancing in
    the first string x (move to dp[i-1][j]).
    """

    n = len(x)
    m = len(y)

    # dp[i][j] = LCS length of x[:i] and y[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # predecessor[i][j]:
    #   "diag" -> matched x[i-1] with y[j-1]
    #   "up"   -> advance in first string
    #   "left"  -> advance in second string
    predecessor = [[None] * (m + 1) for _ in range(n + 1)]

    # Fill the DP table.
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                predecessor[i][j] = "diag"

            elif dp[i - 1][j] >= dp[i][j - 1]:
                # IMPORTANT:
                # >= means ties prefer advancing in x.
                dp[i][j] = dp[i - 1][j]
                predecessor[i][j] = "up"

            else:
                dp[i][j] = dp[i][j - 1]
                predecessor[i][j] = "left"

    # Reconstruct the LCS using predecessors.
    result = []
    i, j = n, m

    while i > 0 and j > 0:
        move = predecessor[i][j]

        if move == "diag":
            result.append(x[i - 1])
            i -= 1
            j -= 1

        elif move == "up":
            i -= 1

        elif move == "left":
            j -= 1

    result.reverse()

    return dp[n][m], "".join(result)


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def is_subsequence(s: str, t: str) -> bool:
    """Return True if s is a subsequence of t."""
    index = 0

    for char in t:
        if index < len(s) and s[index] == char:
            index += 1

    return index == len(s)


def run_tests() -> None:
    # Basic correctness tests.
    assert lcs("ABCBDAB", "BDCABA") == (4, "BCBA")
    assert lcs("AGGTAB", "GXTXAYB") == (4, "GTAB")

    # Empty strings.
    assert lcs("", "ABC") == (0, "")
    assert lcs("ABC", "") == (0, "")
    assert lcs("", "") == (0, "")

    # Identical strings.
    assert lcs("ABC", "ABC") == (3, "ABC")

    # No common characters.
    assert lcs("ABC", "DEF") == (0, "")

    # Repeated characters.
    assert lcs("AAAA", "AA") == (2, "AA")

    # -----------------------------------------------------
    # Critical tie-breaking regression test.
    # -----------------------------------------------------
    #
    # Both "A" and "B" have LCS length 1.
    # At the tie, the required rule prefers advancing
    # in the first string, resulting in "A".
    assert lcs("AB", "BA") == (1, "A")

    # Another deterministic tie case.
    assert lcs("BA", "AB") == (1, "B")

    # Verify general LCS properties.
    cases = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("ABCD", "ACBD"),
        ("AAAA", "AA"),
        ("AB", "BA"),
        ("BA", "AB"),
    ]

    for x, y in cases:
        length, subsequence = lcs(x, y)

        assert length == len(subsequence)
        assert is_subsequence(subsequence, x)
        assert is_subsequence(subsequence, y)


if __name__ == "__main__":
    run_tests()