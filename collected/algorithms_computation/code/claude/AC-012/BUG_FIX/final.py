"""
Problem
-------
Given two strings s1 and s2, compute the length of their Longest Common
Subsequence (LCS) and reconstruct one concrete LCS string.

Determinism rule
-----------------
When reconstructing the LCS by walking the DP table backwards, ties can
occur: at a given cell (i, j) where s1[i-1] != s2[j-1], dp[i-1][j] and
dp[i][j-1] may be equal. In that case we deterministically prefer to
"advance in the first string", i.e. we move to dp[i-1][j] (consuming a
character of s1) rather than dp[i][j-1]. This guarantees the same LCS
is produced on every run for the same inputs.

Constraints
-----------
- Inputs are two strings s1, s2 (may be empty, may contain any characters).
- Must run in O(len(s1) * len(s2)) time and space using classic
  quadratic dynamic programming.
- No randomness, no external services, no I/O beyond returning results.
- Standard library only.

Output
------
A tuple (lcs_length, lcs_string):
- lcs_length: int, the length of the LCS.
- lcs_string: str, one deterministic LCS consistent with the tie-break rule.

Algorithm
---------
1. Build dp table of size (m+1) x (n+1) where dp[i][j] = length of LCS of
   s1[:i] and s2[:j], using the standard recurrence:
     dp[i][j] = dp[i-1][j-1] + 1                  if s1[i-1] == s2[j-1]
     dp[i][j] = max(dp[i-1][j], dp[i][j-1])       otherwise
2. Reconstruct the LCS by starting at (m, n) and walking backwards:
   - If characters match, take the character, move to (i-1, j-1).
   - Else if dp[i-1][j] >= dp[i][j-1], move to (i-1, j)  (prefer advancing s1).
   - Else move to (i, j-1).
3. Reverse the collected characters to get the LCS in correct order.
"""

def lcs(s1: str, s2: str) -> tuple[int, str]:
    m, n = len(s1), len(s2)

    # dp[i][j] = LCS length of s1[:i] and s2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = dp[i - 1][j] if dp[i - 1][j] >= dp[i][j - 1] else dp[i][j - 1]

    # Reconstruct one LCS deterministically
    i, j = m, n
    chars = []
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            # Tie or first string has the better (or equal) option: advance in s1
            i -= 1
        else:
            j -= 1

    chars.reverse()
    lcs_str = "".join(chars)
    return dp[m][n], lcs_str


if __name__ == "__main__":
    tests = [
        ("ABCBDAB", "BDCABA"),
        ("", "ABC"),
        ("ABC", ""),
        ("AGGTAB", "GXTXAYB"),
        ("AAAA", "AA"),
        ("ABC", "ABC"),
    ]
    for a, b in tests:
        length, seq = lcs(a, b)
        print(f"s1={a!r} s2={b!r} -> length={length}, lcs={seq!r}")