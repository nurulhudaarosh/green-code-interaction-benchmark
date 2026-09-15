def lcs(A: str, B: str, include_operation_summary: bool = False) -> dict:
    """
    Compute the Longest Common Subsequence (LCS) of A and B.

    Original required outputs:
      - length: length of the LCS (int)
      - lcs: one valid LCS string achieving that length
      - dp: the full DP table used to compute the result (for optimality verification)

    Optional feature (only added when include_operation_summary=True):
      - operation_summary: dict with total/match/mismatch decision counts made
        while filling the DP table (m*n cells total).

    When include_operation_summary is False (default), the returned dict
    contains ONLY the original fields, unchanged.
    """
    m, n = len(A), len(B)

    # Standard O(m*n) DP table: dp[i][j] = LCS length of A[:i], B[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    match_decisions = 0
    mismatch_decisions = 0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if A[i - 1] == B[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                match_decisions += 1          # "match, take diagonal"
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                mismatch_decisions += 1        # "mismatch, choose max(up, left)"

    # Reconstruct one valid LCS
    i, j = m, n
    seq = []
    while i > 0 and j > 0:
        if A[i - 1] == B[j - 1]:
            seq.append(A[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    lcs_str = "".join(reversed(seq))

    result = {
        "length": dp[m][n],
        "lcs": lcs_str,
        "dp": dp,
    }

    if include_operation_summary:
        result["operation_summary"] = {
            "total_decisions": match_decisions + mismatch_decisions,  # == m * n
            "match_decisions": match_decisions,
            "mismatch_decisions": mismatch_decisions,
        }

    return result


if __name__ == "__main__":
    A, B = "ABCBDAB", "BDCABA"

    # Original behavior (feature disabled): unchanged fields only
    original = lcs(A, B)
    print("Without feature:", original)

    # With feature enabled: adds operation_summary, everything else unchanged
    with_summary = lcs(A, B, include_operation_summary=True)
    print("With feature:   ", with_summary)