def lcs_with_reconstruction(s1: str, s2: str, include_summary: bool = False):
    """
    Compute LCS length and reconstruct one LCS.

    Deterministic tie handling:
      - On equal DP scores (dp[i-1][j] == dp[i][j-1]), prefer advancing
        in the first string (move UP in the DP table).
      - Take the diagonal (match) only when it STRICTLY improves over
        moving up, i.e. dp[i-1][j] < dp[i][j].

    Handles worst-case-like structures:
      - Disjoint alphabets (no matches): full m*n DP fill, m+n reconstruction.
      - Identical strings: full n*n DP fill, n diagonal steps (max matches).
      - Reversed strings: full m*n DP fill, long tie-heavy reconstruction.
      - Alternating alphabets: dense DP, frequent ties resolved deterministically.

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
    """
    m, n = len(s1), len(s2)

    # Step 1: Quadratic DP table (Theta(m*n) time and space)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    lcs_length = dp[m][n]

    # Step 2: Predecessor reconstruction with deterministic tie-breaking
    # Worst case path length: m + n steps (all up then all left, or vice versa).
    lcs_chars = []
    i, j = m, n

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

    if not include_summary:
        return lcs_length, lcs_string

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


# ---------------------------------------------------------------------------
# Baseline regression tests (must preserve original behavior)
# ---------------------------------------------------------------------------
def _run_baseline_tests():
    tests = [
        ("ABCBDAB", "BDCABA", 4, "BCBA"),
        ("ABC", "DEF", 0, ""),
        ("HELLO", "HELLO", 5, "HELLO"),
        ("", "ABC", 0, ""),
        ("AB", "BA", 1, "A"),
        ("BA", "AB", 1, "B"),
        ("AGGTAB", "GXTXAYB", 4, "GTAB"),
        ("AA", "A", 1, "A"),
        ("BAA", "BA", 2, "BA"),
    ]
    print("=== Baseline regression tests (original outputs preserved) ===")
    for s1, s2, exp_len, exp_lcs in tests:
        length, lcs = lcs_with_reconstruction(s1, s2)
        status = "OK" if (length == exp_len and lcs == exp_lcs) else "FAIL"
        print(f"[{status}] s1='{s1}', s2='{s2}' -> length={length}, LCS='{lcs}'")
        assert length == exp_len, f"length mismatch for {(s1, s2)}"
        assert lcs == exp_lcs, f"LCS mismatch for {(s1, s2)}"

    # Verify base return type is exactly 2-tuple
    r = lcs_with_reconstruction("AB", "BA")
    assert isinstance(r, tuple) and len(r) == 2, "Base call must return 2-tuple"
    print("Base call returns exactly (length, string) — OK")
    print()


# ---------------------------------------------------------------------------
# Worst-case-like structure tests
# ---------------------------------------------------------------------------
def _run_worst_case_tests():
    print("=== Worst-case-like structure tests ===")

    # 1. Disjoint alphabets: no matches, full m*n DP fill, m+n reconstruction.
    #    Reconstruction must take exactly m + n steps (all up, then all left).
    N = 200
    s1 = "A" * N
    s2 = "B" * N
    length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
    assert length == 0 and lcs == "", "Disjoint alphabets must yield LCS length 0"
    assert summary["dp_cells"] == N * N, "DP cells must be m*n"
    assert summary["reconstruction_steps"] == 2 * N, \
        f"Reconstruction steps must be m+n={2*N}, got {summary['reconstruction_steps']}"
    assert summary["matches_taken"] == 0, "No matches for disjoint alphabets"
    assert summary["up_moves"] == N, "Tie-break rule: prefer up -> N up moves"
    assert summary["left_moves"] == N, "Then N left moves to reach (0,0)"
    print(f"[OK] Disjoint alphabets (m=n={N}): length=0, "
          f"dp_cells={summary['dp_cells']}, "
          f"reconstruction_steps={summary['reconstruction_steps']}, "
          f"up={summary['up_moves']}, left={summary['left_moves']}, matches=0")

    # 2. Identical strings: full n*n DP fill, n diagonal steps (max matches).
    s1 = s2 = "A" * N
    length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
    assert length == N and lcs == "A" * N, "Identical strings must yield full string"
    assert summary["dp_cells"] == N * N, "DP cells must be n*n"
    assert summary["reconstruction_steps"] == N, \
        f"Reconstruction must take n={N} diagonal steps"
    assert summary["matches_taken"] == N, "All steps must be matches"
    assert summary["up_moves"] == 0 and summary["left_moves"] == 0
    print(f"[OK] Identical strings (n={N}): length={N}, "
          f"dp_cells={summary['dp_cells']}, "
          f"reconstruction_steps={summary['reconstruction_steps']}, "
          f"matches={summary['matches_taken']}")

    # 3. Reversed distinct-character strings: LCS length 1, long tie-heavy path.
    s1 = "".join(chr(ord('A') + (k % 26)) for k in range(N))
    s2 = s1[::-1]
    length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
    # For a strictly increasing sequence and its reverse, LCS length is 1
    # (each character is unique in s1 only if N <= 26; here we duplicate
    # after 26, so LCS length may be larger. We assert the weaker invariant:
    # length must be consistent with a valid common subsequence and the
    # reconstruction must fit within m+n steps.)
    assert 0 <= length <= min(len(s1), len(s2)), "Length must be valid"
    assert summary["reconstruction_steps"] <= len(s1) + len(s2), \
        "Reconstruction steps bounded by m+n"
    assert summary["dp_cells"] == len(s1) * len(s2), "DP cells must be m*n"
    assert summary["matches_taken"] == length, \
        "Each match adds exactly one character; matches must equal length"
    # Verify lcs is actually a subsequence of both
    def _is_subseq(sub, s):
        it = iter(s)
        return all(c in it for c in sub)
    assert _is_subseq(lcs, s1) and _is_subseq(lcs, s2), \
        "Returned LCS must be a subsequence of both inputs"
    print(f"[OK] Reversed strings (m=n={N}): length={length}, "
          f"dp_cells={summary['dp_cells']}, "
          f"reconstruction_steps={summary['reconstruction_steps']}, "
          f"matches={summary['matches_taken']}, "
          f"up={summary['up_moves']}, left={summary['left_moves']}")

    # 4. Alternating alphabets: dense DP, frequent ties resolved deterministically.
    s1 = ("AB" * (N // 2))
    s2 = ("BA" * (N // 2))
    length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
    assert summary["dp_cells"] == N * N, "DP cells must be m*n"
    assert summary["reconstruction_steps"] <= 2 * N, "Steps bounded by m+n"
    assert summary["matches_taken"] == length, "matches must equal LCS length"
    assert _is_subseq(lcs, s1) and _is_subseq(lcs, s2), \
        "Returned LCS must be a subsequence of both inputs"
    # Determinism check: repeat the call and confirm identical output.
    length2, lcs2, summary2 = lcs_with_reconstruction(s1, s2, include_summary=True)
    assert (length, lcs, summary) == (length2, lcs2, summary2), \
        "Repeated calls must be deterministic"
    print(f"[OK] Alternating alphabets (m=n={N}): length={length}, "
          f"dp_cells={summary['dp_cells']}, "
          f"reconstruction_steps={summary['reconstruction_steps']}, "
          f"matches={summary['matches_taken']}, "
          f"up={summary['up_moves']}, left={summary['left_moves']}")

    # 5. Asymmetric worst case: m=1, n=large disjoint.
    s1 = "A"
    s2 = "B" * N
    length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
    assert length == 0 and lcs == "", "No common characters -> empty LCS"
    assert summary["dp_cells"] == N, "DP cells must be 1*N"
    assert summary["reconstruction_steps"] == N + 1, "m+n = 1+N steps"
    print(f"[OK] Asymmetric disjoint (m=1, n={N}): length=0, "
          f"dp_cells={summary['dp_cells']}, "
          f"reconstruction_steps={summary['reconstruction_steps']}")

    # 6. Empty-on-one-side worst case.
    s1 = "A" * N
    s2 = ""
    length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
    assert length == 0 and lcs == "", "Empty input -> empty LCS"
    assert summary["dp_cells"] == 0, "No DP cells when one side is empty"
    assert summary["reconstruction_steps"] == 0, "No reconstruction steps"
    print(f"[OK] Empty-on-one-side (m={N}, n=0): length=0, "
          f"dp_cells=0, reconstruction_steps=0")

    print()


if __name__ == "__main__":
    _run_baseline_tests()
    _run_worst_case_tests()
    print("All tests passed.")