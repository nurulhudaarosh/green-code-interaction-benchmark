"""
Longest Common Subsequence with deterministic reconstruction.

Tie-break rule (preserved): on equal DP scores during reconstruction,
prefer advancing in the FIRST string (move up: i -= 1).
"""

from array import array


def lcs_length_and_sequence(s1: str, s2: str):
    """
    Return (lcs_length, lcs_string).

    Time:  O(m * n)
    Space: O(m * n) using 2-byte unsigned shorts when possible,
           else Python ints (fallback for very long LCS).
    """
    m, n = len(s1), len(s2)
    if m == 0 or n == 0:
        return 0, ""

    # Choose storage: array('H') uses 2 bytes/cell (max value 65535).
    # If the LCS could exceed 65535, fall back to lists of ints.
    max_possible = min(m, n)
    if max_possible <= 0xFFFF:
        def new_row():
            return array('H', [0]) * (n + 1)
        dp = [new_row() for _ in range(m + 1)]
    else:
        dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Build DP table.
    # dp[i][j] = LCS(s1[:i], s2[:j])
    for i in range(1, m + 1):
        c1 = s1[i - 1]
        row = dp[i]
        prev = dp[i - 1]
        for j in range(1, n + 1):
            if c1 == s2[j - 1]:
                row[j] = prev[j - 1] + 1
            else:
                up = prev[j]
                left = row[j - 1]
                row[j] = up if up >= left else left

    lcs_len = dp[m][n]

    # Reconstruct one LCS walking backwards.
    # Tie-break: if dp[i-1][j] >= dp[i][j-1], move up (first string).
    chars = []
    i, j = m, n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            chars.append(s1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    chars.reverse()
    return lcs_len, "".join(chars)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def _run_case(name, s1, s2, expected_len=None, expected_seq=None):
    length, seq = lcs_length_and_sequence(s1, s2)
    status = "OK"
    if expected_len is not None and length != expected_len:
        status = f"FAIL len (got {length}, want {expected_len})"
    if expected_seq is not None and seq != expected_seq:
        status = f"FAIL seq (got {seq!r}, want {expected_seq!r})"
    print(f"[{status}] {name}: len={length} seq={seq!r}")
    return status == "OK"


def run_all_tests():
    all_ok = True

    # --- Original cases (preserve original outputs & tie-breaking) ---
    all_ok &= _run_case("classic ABCBDAB/BDCABA",
                        "ABCBDAB", "BDCABA", 4, "BCBA")
    all_ok &= _run_case("AGGTAB/GXTXAYB",
                        "AGGTAB", "GXTXAYB", 4, "GTAB")
    all_ok &= _run_case("empty left", "", "ABC", 0, "")
    all_ok &= _run_case("empty right", "ABC", "", 0, "")
    all_ok &= _run_case("AAAA/AA", "AAAA", "AA", 2, "AA")
    all_ok &= _run_case("identical", "ABC", "ABC", 3, "ABC")
    all_ok &= _run_case("disjoint", "ABC", "DEF", 0, "")

    # --- Hard / difficult cases ---

    # 1. All-equal characters: every step is diagonal.
    m, n = 2000, 2000
    s1 = "A" * m
    s2 = "A" * n
    all_ok &= _run_case(f"all-equal {m}x{n}",
                        s1, s2, min(m, n), "A" * min(m, n))

    # 2. No common characters: every step is an up/left tie.
    #    Tie-break must always prefer "up" (first string).
    s1 = "A" * 1500
    s2 = "B" * 1500
    all_ok &= _run_case("no-common 1500x1500",
                        s1, s2, 0, "")

    # 3. Anti-diagonal / repetitive: many equal-score plateaus.
    k = 800
    s1 = "AB" * k
    s2 = "BA" * k
    length, seq = lcs_length_and_sequence(s1, s2)
    # Sanity: seq must be a subsequence of both, length consistent.
    def is_subseq(sub, full):
        it = iter(full)
        return all(ch in it for ch in sub)
    ok = (is_subseq(seq, s1) and is_subseq(seq, s2)
          and length == len(seq))
    print(f"[{'OK' if ok else 'FAIL'}] anti-diagonal 2*{k}: "
          f"len={length} seq_prefix={seq[:20]!r}...")
    all_ok &= ok

    # 4. Asymmetric lengths: one string much longer.
    s1 = "ABCDEFGH" * 500          # 4000 chars
    s2 = "AHD"                     # 3 chars
    all_ok &= _run_case("asymmetric long/short",
                        s1, s2, 3, "AHD")

    # 5. Maximum-density worst-case for tie-break rule:
    #    s1 and s2 share no characters but are long, so every
    #    reconstruction step is a tie. Verify determinism by
    #    running twice and comparing.
    s1 = "XY" * 1000
    s2 = "AB" * 1000
    r1 = lcs_length_and_sequence(s1, s2)
    r2 = lcs_length_and_sequence(s1, s2)
    det_ok = (r1 == r2 == (0, ""))
    print(f"[{'OK' if det_ok else 'FAIL'}] determinism on tie-heavy case: {r1}")
    all_ok &= det_ok

    # 6. Known tie case verifying the rule "prefer up on ties".
    #    s1="AB", s2="BA": dp table has a tie at (2,2); rule picks 'A'.
    all_ok &= _run_case("tie AB/BA prefers first string",
                        "AB", "BA", 1, "A")

    # 7. Single-character overlap in long strings.
    s1 = "Z" * 1000 + "Q"
    s2 = "Q" + "Z" * 1000
    all_ok &= _run_case("single overlap long",
                        s1, s2, 1, "Q")

    print()
    print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")
    return all_ok


if __name__ == "__main__":
    run_all_tests()