from typing import Dict, Any


def lcs(x: str, y: str, include_operation_summary: bool = False) -> Dict[str, Any]:
    """
    Compute the Longest Common Subsequence of two strings.

    Returns the original LCS results:
        - lcs_length
        - lcs

    When include_operation_summary=True, also returns:
        - operation_summary

    Tie-breaking rule:
        If dp[i-1][j] == dp[i][j-1], prefer advancing
        in the first string x (move "up").
    """

    n = len(x)
    m = len(y)

    # DP table:
    # dp[i][j] = LCS length of x[:i] and y[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Predecessor table:
    # "diag" -> characters matched
    # "up"   -> advance in first string
    # "left" -> advance in second string
    predecessor = [[None] * (m + 1) for _ in range(n + 1)]

    # Count one major operation for every non-base DP cell.
    operation_count = 0

    # Fill the DP table.
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            operation_count += 1

            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                predecessor[i][j] = "diag"

            elif dp[i - 1][j] >= dp[i][j - 1]:
                # On a tie, prefer advancing in x.
                dp[i][j] = dp[i - 1][j]
                predecessor[i][j] = "up"

            else:
                dp[i][j] = dp[i][j - 1]
                predecessor[i][j] = "left"

    # Reconstruct one LCS.
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
    lcs_string = "".join(result)

    # Preserve the original outputs.
    output = {
        "lcs_length": dp[n][m],
        "lcs": lcs_string,
    }

    # Add the new field only when requested.
    if include_operation_summary:
        output["operation_summary"] = {
            "major_operations": operation_count
        }

    return output


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def is_subsequence(s: str, t: str) -> bool:
    """Check whether s is a subsequence of t."""
    i = 0

    for char in t:
        if i < len(s) and s[i] == char:
            i += 1

    return i == len(s)


def run_tests() -> None:

    # Original behavior when the feature is disabled.
    assert lcs("ABCBDAB", "BDCABA") == {
        "lcs_length": 4,
        "lcs": "BCBA",
    }

    assert lcs("AGGTAB", "GXTXAYB") == {
        "lcs_length": 4,
        "lcs": "GTAB",
    }

    # Empty strings.
    assert lcs("", "ABC") == {
        "lcs_length": 0,
        "lcs": "",
    }

    assert lcs("ABC", "") == {
        "lcs_length": 0,
        "lcs": "",
    }

    # No common subsequence except the empty string.
    assert lcs("ABC", "DEF") == {
        "lcs_length": 0,
        "lcs": "",
    }

    # Identical strings.
    assert lcs("ABC", "ABC") == {
        "lcs_length": 3,
        "lcs": "ABC",
    }

    # Deterministic tie-breaking regression test.
    #
    # Both "A" and "B" are valid LCSs of length 1.
    # The required rule prefers moving "up", producing "A".
    assert lcs("AB", "BA") == {
        "lcs_length": 1,
        "lcs": "A",
    }

    # -----------------------------------------------------
    # New operation_summary tests.
    # -----------------------------------------------------

    result = lcs(
        "ABC",
        "DEF",
        include_operation_summary=True
    )

    assert result == {
        "lcs_length": 0,
        "lcs": "",
        "operation_summary": {
            "major_operations": 3 * 3
        },
    }

    result = lcs(
        "ABCD",
        "ACBD",
        include_operation_summary=True
    )

    assert result["lcs_length"] == 3
    assert result["lcs"] == "ABD"
    assert result["operation_summary"] == {
        "major_operations": 4 * 4
    }

    # Empty inputs have no non-base DP cells.
    result = lcs("", "", include_operation_summary=True)

    assert result == {
        "lcs_length": 0,
        "lcs": "",
        "operation_summary": {
            "major_operations": 0
        },
    }

    # Verify that the returned LCS is valid.
    test_cases = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("AAAA", "AA"),
        ("AB", "BA"),
        ("BA", "AB"),
    ]

    for x, y in test_cases:
        result = lcs(x, y, include_operation_summary=True)

        assert result["lcs_length"] == len(result["lcs"])
        assert is_subsequence(result["lcs"], x)
        assert is_subsequence(result["lcs"], y)

        # Exactly one major operation per DP cell.
        assert (
            result["operation_summary"]["major_operations"]
            == len(x) * len(y)
        )


if __name__ == "__main__":
    run_tests()