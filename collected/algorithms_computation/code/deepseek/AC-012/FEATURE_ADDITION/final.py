def lcs(s1: str, s2: str, include_summary: bool = False):
    """
    Compute LCS length and one deterministic LCS.

    If include_summary is True, also return an `operation_summary` dict
    with counts of major computational decisions/operations.
    If False, behavior is identical to the original function.
    """
    m, n = len(s1), len(s2)

    # --- DP table construction ---
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    dp_cells = 0
    match_decisions = 0
    mismatch_decisions = 0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp_cells += 1
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                match_decisions += 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                mismatch_decisions += 1

    length = dp[m][n]

    # --- Deterministic reconstruction ---
    i, j = m, n
    chars = []
    backtrack_steps = 0
    tie_breaks = 0

    while i > 0 and j > 0:
        backtrack_steps += 1
        if s1[i - 1] == s2[j - 1]:
            chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        elif dp[i - 1][j] < dp[i][j - 1]:
            j -= 1
        else:
            # Equal scores: deterministic rule prefers advancing in s1
            tie_breaks += 1
            i -= 1

    lcs_str = ''.join(reversed(chars))

    if not include_summary:
        return length, lcs_str

    operation_summary = {
        "dp_cells_evaluated": dp_cells,
        "match_decisions": match_decisions,
        "mismatch_decisions": mismatch_decisions,
        "backtrack_steps": backtrack_steps,
        "backtrack_tie_breaks": tie_breaks,
        "total_major_operations": (
            dp_cells + match_decisions + mismatch_decisions
            + backtrack_steps + tie_breaks
        ),
    }

    return length, lcs_str, operation_summary


if __name__ == "__main__":
    tests = [
        ("ABCBDAB", "BDCABA"),
        ("AGGTAB", "GXTXAYB"),
        ("", "ABC"),
        ("ABC", ""),
        ("ABC", "ABC"),
        ("ABC", "DEF"),
        ("XMJYAUZ", "MZJAWXU"),
    ]

    print("=== Original behavior (feature disabled) ===")
    for a, b in tests:
        length, seq = lcs(a, b)
        print(f"LCS({a!r}, {b!r}) -> length={length}, sequence={seq!r}")

    print()
    print("=== Extended behavior (feature enabled) ===")
    for a, b in tests:
        length, seq, summary = lcs(a, b, include_summary=True)
        print(f"LCS({a!r}, {b!r}) -> length={length}, sequence={seq!r}")
        print(f"    operation_summary = {summary}")