"""
Longest Common Subsequence (LCS) — deterministic quadratic DP solution
========================================================================

PROBLEM
-------
Given two strings s1 and s2, compute:
  1. The length of their Longest Common Subsequence (LCS).
  2. One valid LCS string, reconstructed using a *deterministic* tie-breaking
     rule so that the same inputs always yield the same output (required
     because in general there can be multiple distinct LCSs of the same
     maximal length).

CONSTRAINTS
-----------
- Inputs are two finite strings s1 (length n) and s2 (length m).
- Only standard library is used; no network access, no randomness,
  no external services, no human interaction.
- Must run in O(n*m) time / O(n*m) space (quadratic DP), which is the
  standard optimal-substructure approach for LCS.
- Reconstruction must be deterministic: whenever there is a tie between
  moving in s1 vs. s2 during backtracking (i.e. dp[i-1][j] == dp[i][j-1]),
  the algorithm must prefer to advance in the FIRST string.

REQUIRED OUTPUT
----------------
- lcs_length: int, the length of the LCS.
- lcs_string: str, one valid LCS matching that length, produced by the
  deterministic rule above.

ALGORITHM
---------
1. Build a (n+1) x (m+1) DP table `dp` where dp[i][j] = length of the LCS
   of s1[:i] and s2[:j].
   Recurrence:
     dp[i][j] = dp[i-1][j-1] + 1              if s1[i-1] == s2[j-1]
     dp[i][j] = max(dp[i-1][j], dp[i][j-1])   otherwise
   Base case: dp[0][*] = dp[*][0] = 0.
2. dp[n][m] is the LCS length.
3. Reconstruct one LCS by walking backwards from (n, m) to (0, 0):
     - If s1[i-1] == s2[j-1]: this character belongs to the LCS;
       prepend it and move to (i-1, j-1).
     - Else if dp[i-1][j] > dp[i][j-1]: move to (i-1, j)  (advance in s1)
     - Else if dp[i][j-1] > dp[i-1][j]: move to (i, j-1)  (advance in s2)
     - Else (TIE, dp[i-1][j] == dp[i][j-1]): move to (i-1, j)
       — i.e. deterministically prefer advancing in the FIRST string.
"""

from typing import Tuple


def lcs(s1: str, s2: str) -> Tuple[int, str]:
    """
    Compute the LCS length and one deterministic LCS string for s1, s2.

    Tie-breaking rule during reconstruction: when dp[i-1][j] == dp[i][j-1],
    prefer advancing in the first string (s1).

    Returns:
        (lcs_length, lcs_string)
    """
    n, m = len(s1), len(s2)

    # dp[i][j] = LCS length of s1[:i] and s2[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        ci = s1[i - 1]
        row_i, row_im1 = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            if ci == s2[j - 1]:
                row_i[j] = row_im1[j - 1] + 1
            else:
                a, b = row_im1[j], row_i[j - 1]
                row_i[j] = a if a >= b else b

    lcs_length = dp[n][m]

    # Deterministic backtracking to reconstruct one LCS.
    chars = []
    i, j = n, m
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            chars.append(s1[i - 1])
            i -= 1
            j -= 1
        else:
            up = dp[i - 1][j]      # score if we advance in s1 (move i)
            left = dp[i][j - 1]    # score if we advance in s2 (move j)
            if up >= left:
                # Strictly better in s1, OR a tie -> prefer advancing in s1.
                i -= 1
            else:
                j -= 1

    chars.reverse()
    lcs_string = "".join(chars)

    return lcs_length, lcs_string


def _self_test() -> None:
    """Small deterministic sanity checks (no randomness, no I/O side effects)."""
    cases = [
        ("", "", 0, ""),
        ("abc", "", 0, ""),
        ("", "abc", 0, ""),
        ("abcde", "ace", 3, "ace"),
        ("AGGTAB", "GXTXAYB", 4, "GTAB"),
        ("abc", "abc", 3, "abc"),
        ("abc", "def", 0, ""),
    ]
    for s1, s2, exp_len, exp_str in cases:
        length, s = lcs(s1, s2)
        assert length == exp_len, f"lcs({s1!r},{s2!r}) length {length} != {exp_len}"
        assert s == exp_str, f"lcs({s1!r},{s2!r}) string {s!r} != {exp_str!r}"
    print("All self-tests passed.")


def main() -> None:
    _self_test()

    examples = [
        ("ABCBDAB", "BDCABA"),
        ("XMJYAUZ", "MZJAWXU"),
        ("HUMAN", "CHIMPANZEE"),
    ]
    for s1, s2 in examples:
        length, s = lcs(s1, s2)
        print(f"s1={s1!r}, s2={s2!r} -> lcs_length={length}, lcs_string={s!r}")


if __name__ == "__main__":
    main()