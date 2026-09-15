"""
PROBLEM
-------
Given two strings s1 and s2, compute the length of their Longest Common
Subsequence (LCS) and reconstruct ONE concrete LCS string.

Because multiple different LCS strings can share the same (maximum) length,
we need a DETERMINISTIC tie-breaking rule so the output is always the same
for the same input. Rule used here:

    While reconstructing backwards through the DP table, whenever a
    non-matching cell has two predecessor cells with EQUAL DP scores
    (dp[i-1][j] == dp[i][j-1]), we prefer the move that advances the
    pointer in the FIRST string (i.e. we step i -> i-1, effectively
    keeping/consuming more of s1 first) rather than stepping in s2.

CONSTRAINTS
------------
- Inputs: two strings s1, s2 (may be empty, may contain any characters).
- Must use classic O(n*m) time / O(n*m) space quadratic DP.
- No randomness, no network/API calls, no external libraries, no user
  interaction beyond an optional __main__ demo — deterministic, pure
  standard-library Python only.
- Output: the integer LCS length, and one valid LCS string chosen by the
  deterministic rule above.

ALGORITHM
---------
1. Build dp table of size (n+1) x (m+1), where
       dp[i][j] = length of LCS of s1[:i] and s2[:j]
   Recurrence:
       dp[0][j] = dp[i][0] = 0
       if s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1
       else:                  dp[i][j] = max(dp[i-1][j], dp[i][j-1])
2. dp[n][m] is the LCS length.
3. Reconstruct by walking from (n, m) back to (0, 0):
       - if s1[i-1] == s2[j-1]: this char is part of the LCS;
         prepend it, move to (i-1, j-1)
       - else if dp[i-1][j] >= dp[i][j-1]: move to (i-1, j)   <-- tie -> prefer s1 advance
       - else: move to (i, j-1)
   This produces a single deterministic LCS string.
"""

from typing import Tuple


def lcs(s1: str, s2: str) -> Tuple[int, str]:
    """Compute LCS length and one deterministic LCS string of s1, s2."""
    n, m = len(s1), len(s2)

    # dp[i][j] = LCS length of s1[:i] and s2[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        ci = s1[i - 1]
        row, prev_row = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            if ci == s2[j - 1]:
                row[j] = prev_row[j - 1] + 1
            else:
                a = prev_row[j]
                b = row[j - 1]
                row[j] = a if a >= b else b

    length = dp[n][m]

    # Reconstruction with deterministic tie-breaking.
    chars = []
    i, j = n, m
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            chars.append(s1[i - 1])
            i -= 1
            j -= 1
        else:
            up = dp[i - 1][j]     # advancing in s1
            left = dp[i][j - 1]   # advancing in s2
            if up >= left:        # tie or better -> prefer advancing in s1
                i -= 1
            else:
                j -= 1

    chars.reverse()
    return length, "".join(chars)


if __name__ == "__main__":
    tests = [
        ("ABCBDAB", "BDCABA"),
        ("", ""),
        ("abc", ""),
        ("", "xyz"),
        ("AGGTAB", "GXTXAYB"),
        ("aaaa", "aa"),
    ]
    for a, b in tests:
        length, subseq = lcs(a, b)
        print(f"s1={a!r} s2={b!r} -> length={length}, lcs={subseq!r}")