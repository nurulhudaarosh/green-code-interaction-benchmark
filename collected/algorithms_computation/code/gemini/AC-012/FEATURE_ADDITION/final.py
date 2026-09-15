def lcs_with_reconstruction(
    s1: str, s2: str, include_summary: bool = False
) -> tuple[int, str] | tuple[int, str, dict[str, int]]:
    """
    Computes the LCS length and reconstructs one LCS string deterministically.
    Prefers advancing in s1 (moving i -> i-1) when DP scores are equal.

    Optionally returns an `operation_summary` dictionary detailing key operations.
    """
    m, n = len(s1), len(s2)

    # Operational metrics
    dp_cell_updates = m * n
    match_operations = 0
    mismatch_operations = 0
    backtrack_steps = 0
    tie_break_decisions = 0

    # Step 1: Build the DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                match_operations += 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                mismatch_operations += 1

    lcs_length = dp[m][n]

    # Step 2: Reconstruct the sequence using the deterministic rule
    lcs_chars = []
    i, j = m, n

    while i > 0 and j > 0:
        backtrack_steps += 1
        if s1[i - 1] == s2[j - 1]:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        elif dp[i - 1][j] < dp[i][j - 1]:
            j -= 1
        else:
            # Equal DP scores: tie-break decision preference (advance in s1 -> decrement i)
            tie_break_decisions += 1
            i -= 1

    # Clear remaining edges if backtrack reaches boundary (i=0 or j=0)
    while i > 0:
        backtrack_steps += 1
        i -= 1
    while j > 0:
        backtrack_steps += 1
        j -= 1

    reconstructed_lcs = "".join(reversed(lcs_chars))

    if include_summary:
        operation_summary = {
            "dp_cell_updates": dp_cell_updates,
            "match_operations": match_operations,
            "mismatch_operations": mismatch_operations,
            "backtrack_steps": backtrack_steps,
            "tie_break_decisions": tie_break_decisions,
        }
        return lcs_length, reconstructed_lcs, operation_summary

    return lcs_length, reconstructed_lcs


# Example usage
if __name__ == "__main__":
    str1 = "ABCBDAB"
    str2 = "BDCABA"

    # Original signature (backward compatible)
    length, lcs_str = lcs_with_reconstruction(str1, str2)
    print(f"Original Return -> Length: {length}, String: '{lcs_str}'")

    # Extended signature with operational summary
    length, lcs_str, summary = lcs_with_reconstruction(
        str1, str2, include_summary=True
    )
    print(f"\nExtended Return -> Length: {length}, String: '{lcs_str}'")
    print("Operation Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")