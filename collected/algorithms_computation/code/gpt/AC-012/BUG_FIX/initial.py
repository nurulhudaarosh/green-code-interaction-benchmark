from typing import Tuple


def lcs(a: str, b: str) -> Tuple[int, str]:
    """
    Compute the LCS length and reconstruct one deterministic LCS.

    Tie-breaking rule:
        When dp[i + 1][j] == dp[i][j + 1], prefer advancing
        in the first string (i.e., move from i to i + 1).

    Returns:
        (lcs_length, lcs_string)
    """

    n = len(a)
    m = len(b)

    # dp[i][j] = LCS length of a[i:] and b[j:].
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Fill the DP table from bottom-right to top-left.
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if a[i] == b[j]:
                dp[i][j] = 1 + dp[i + 1][j + 1]
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])

    # Reconstruct one LCS.
    result = []
    i = 0
    j = 0

    while i < n and j < m:
        if a[i] == b[j]:
            result.append(a[i])
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            # Equal scores -> prefer advancing in the first string.
            i += 1
        else:
            j += 1

    return dp[0][0], "".join(result)


# -------------------------
# Tests
# -------------------------

def run_tests() -> None:
    test_cases = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("ABC", "ABC"),
        ("ABC", "DEF"),
        ("", "ABC"),
        ("ABC", ""),
        ("AAAA", "AA"),
    ]

    for a, b in test_cases:
        length, sequence = lcs(a, b)

        assert length == len(sequence), (
            f"Length mismatch for {a!r}, {b!r}"
        )

        # Verify that the returned sequence is a subsequence of both strings.
        def is_subsequence(s: str, target: str) -> bool:
            it = iter(target)
            return all(char in it for char in s)

        assert is_subsequence(sequence, a), (
            f"{sequence!r} is not a subsequence of {a!r}"
        )
        assert is_subsequence(sequence, b), (
            f"{sequence!r} is not a subsequence of {b!r}"
        )

    # Known LCS lengths.
    assert lcs("ABCBDAB", "BDCABA")[0] == 4
    assert lcs("AGGTAB", "GXTXAYB")[0] == 4
    assert lcs("ABC", "ABC") == (3, "ABC")
    assert lcs("ABC", "DEF") == (0, "")
    assert lcs("", "ABC") == (0, "")
    assert lcs("ABC", "") == (0, "")
    assert lcs("AAAA", "AA")[0] == 2


if __name__ == "__main__":
    run_tests()

    # Example
    a = "ABCBDAB"
    b = "BDCABA"

    length, sequence = lcs(a, b)

    print("String 1:", a)
    print("String 2:", b)
    print("LCS length:", length)
    print("LCS:", sequence)