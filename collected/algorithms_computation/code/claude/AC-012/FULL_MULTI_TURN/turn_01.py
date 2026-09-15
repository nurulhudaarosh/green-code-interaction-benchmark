"""
Longest Common Subsequence (LCS): length + deterministic reconstruction.

Algorithm: quadratic-time dynamic programming (O(n*m) time and space) plus
backward predecessor reconstruction. When the DP scores for the two possible
predecessor moves are tied, the reconstruction deterministically prefers
advancing the pointer in the FIRST string (A) over the second (B).

Standard library only. No randomness, no I/O beyond the demo in __main__.
"""

from typing import Tuple


def lcs(a: str, b: str) -> Tuple[int, str]:
    """
    Compute the LCS length and one deterministic LCS string for a and b.

    Tie-breaking rule during reconstruction: when dp[i-1][j] >= dp[i][j-1],
    the algorithm moves by decrementing i (advancing in the first string a).
    It only moves by decrementing j (advancing in b) when dp[i][j-1] is
    strictly greater.

    Args:
        a: first string.
        b: second string.

    Returns:
        (length, subsequence) where length is the LCS length and
        subsequence is one valid LCS consistent with the tie-break rule.
    """
    n, m = len(a), len(b)

    # dp[i][j] = LCS length of a[:i] and b[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        ai = a[i - 1]
        row_i, row_im1 = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                row_i[j] = row_im1[j - 1] + 1
            else:
                up = row_im1[j]      # dp[i-1][j]  -> advances a if chosen
                left = row_i[j - 1]  # dp[i][j-1]  -> advances b if chosen
                row_i[j] = up if up >= left else left

    length = dp[n][m]

    # Reconstruct one LCS, walking backward from (n, m).
    chars = []
    i, j = n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            chars.append(a[i - 1])
            i -= 1
            j -= 1
        else:
            up = dp[i - 1][j]
            left = dp[i][j - 1]
            if up >= left:
                # Tie or a-branch strictly better: advance in the first string.
                i -= 1
            else:
                j -= 1

    chars.reverse()
    subsequence = "".join(chars)

    # Sanity check: reconstruction length must match the DP length.
    assert len(subsequence) == length

    return length, subsequence


def _demo() -> None:
    cases = [
        ("ABCBDAB", "BDCABA"),
        ("", "ABC"),
        ("ABC", ""),
        ("AGGTAB", "GXTXAYB"),
        ("AAAA", "AA"),
        ("ABAB", "BABA"),      # exercises the tie-break rule
        ("abc", "abc"),
        ("abc", "xyz"),
    ]
    for a, b in cases:
        length, sub = lcs(a, b)
        print(f"A={a!r:12} B={b!r:12} -> length={length}, lcs={sub!r}")


if __name__ == "__main__":
    _demo()