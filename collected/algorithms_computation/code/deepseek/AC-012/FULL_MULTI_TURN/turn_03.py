def lcs_with_reconstruction(s1: str, s2: str, include_summary: bool = False):
    """
    Compute LCS length and reconstruct one LCS.

    Deterministic tie handling:
      - On equal DP scores (dp[i-1][j] == dp[i][j-1]), prefer advancing
        in the first string (move UP in the DP table).
      - Take the diagonal (match) only when it STRICTLY improves over
        moving up, i.e. dp[i-1][j] < dp[i][j].

    Args:
        s1, s2: input strings.
        include_summary: if True, append an `operation_summary` dict as a
            third element of the returned tuple. If False (default), the
            return value is exactly the original 2-tuple
            (lcs_length, lcs_string).

    Returns:
        If include_summary is False:
            (lcs_length, lcs_string)
        If include_summary is True:
            (lcs_length, lcs_string, operation_summary)
        where operation_summary is a dict with keys:
            dp_cells, reconstruction_steps, matches_taken,
            up_moves, left_moves, total_operations.
    """
    m, n = len(s1), len(s2)

    # Step 1: Quadratic DP table
    # dp[i][j] = LCS length of s1[:i] and s2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_length = dp[m][n]

    # Step 2: Predecessor reconstruction with deterministic tie-breaking
    lcs_chars = []
    i, j = m, n

    # Counters for operation_summary
    reconstruction_steps = 0
    matches_taken = 0
    up_moves = 0
    left_moves = 0

    while i > 0 and j > 0:
        reconstruction_steps += 1
        match = (s1[i - 1] == s2[j - 1])
        diagonal_strictly_better = (
            match
            and dp[i][j] == dp[i - 1][j - 1] + 1
            and dp[i - 1][j] < dp[i][j]
        )
        if diagonal_strictly_better:
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
            matches_taken += 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1  # prefer advancing in s1
            up_moves += 1
        else:
            j -= 1  # advance in s2
            left_moves += 1

    lcs_string = ''.join(reversed(lcs_chars))

    # Base result: unchanged original 2-tuple behavior
    if not include_summary:
        return lcs_length, lcs_string

    # Extended result: original fields + operation_summary
    dp_cells = m * n
    operation_summary = {
        "dp_cells": dp_cells,
        "reconstruction_steps": reconstruction_steps,
        "matches_taken": matches_taken,
        "up_moves": up_moves,
        "left_moves": left_moves,
        "total_operations": dp_cells + reconstruction_steps,
    }
    return lcs_length, lcs_string, operation_summary


if __name__ == "__main__":
    tests = [
        ("ABCBDAB", "BDCABA"),
        ("ABC", "DEF"),
        ("HELLO", "HELLO"),
        ("", "ABC"),
        ("AB", "BA"),
        ("BA", "AB"),
        ("AGGTAB", "GXTXAYB"),
        ("AA", "A"),
        ("BAA", "BA"),
    ]

    print("=== Base behavior (feature disabled / not requested) ===")
    for s1, s2 in tests:
        result = lcs_with_reconstruction(s1, s2)
        assert isinstance(result, tuple) and len(result) == 2, \
            "Base call must return exactly (length, string)"
        length, lcs = result
        print(f"s1='{s1}', s2='{s2}' -> length={length}, LCS='{lcs}'")

    print()
    print("=== Extended behavior (include_summary=True) ===")
    for s1, s2 in tests:
        length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
        print(f"s1='{s1}', s2='{s2}' -> length={length}, LCS='{lcs}'")
        print(f"    operation_summary={summary}")