from typing import Dict, List, Tuple


def lcs(a: str, b: str) -> Dict[str, object]:
    """
    Compute the length of the Longest Common Subsequence (LCS)
    and reconstruct one deterministic LCS.

    Tie-breaking rule:
        When advancing in the first string (i-1) and advancing in
        the second string (j-1) have equal DP scores, prefer
        advancing in the first string.

    Returns:
        {
            "length": int,
            "lcs": str
        }
    """

    m = len(a)
    n = len(b)

    # dp[i][j] = LCS length of a[:i] and b[:j]
    dp: List[List[int]] = [
        [0] * (n + 1)
        for _ in range(m + 1)
    ]

    # predecessor[i][j]:
    #   "diag" -> a[i-1] == b[j-1], take the character
    #   "up"   -> move to (i-1, j), advance in first string
    #   "left" -> move to (i, j-1), advance in second string
    predecessor: List[List[str]] = [
        [""] * (n + 1)
        for _ in range(m + 1)
    ]

    # Build DP table and predecessor table.
    for i in range(1, m + 1):
        for j in range(1, n + 1):

            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                predecessor[i][j] = "diag"

            elif dp[i - 1][j] >= dp[i][j - 1]:
                # Prefer moving in the first string on ties.
                dp[i][j] = dp[i - 1][j]
                predecessor[i][j] = "up"

            else:
                dp[i][j] = dp[i][j - 1]
                predecessor[i][j] = "left"

    # Reconstruct the LCS using predecessor pointers.
    result: List[str] = []

    i, j = m, n

    while i > 0 and j > 0:
        move = predecessor[i][j]

        if move == "diag":
            result.append(a[i - 1])
            i -= 1
            j -= 1

        elif move == "up":
            i -= 1

        elif move == "left":
            j -= 1

        else:
            # This occurs only when reaching an empty prefix.
            break

    result.reverse()

    return {
        "length": dp[m][n],
        "lcs": "".join(result)
    }


# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------

if __name__ == "__main__":
    a = "ABCBDAB"
    b = "BDCABA"

    answer = lcs(a, b)

    print(answer)