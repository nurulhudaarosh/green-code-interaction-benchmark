from typing import List, Tuple


def edit_distance_with_transposition(s1: str, s2: str) -> int:
    """Computes the Optimal String Alignment (OSA) distance between s1 and s2

    with explicit adjacent transposition, handling repeated characters and ties.
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            # Candidate operations
            best_val = min(
                dp[i - 1][j] + 1,  # Deletion
                dp[i][j - 1] + 1,  # Insertion
                dp[i - 1][j - 1] + cost,  # Match or Substitution
            )

            # Explicit adjacent transposition
            if (
                i > 1
                and j > 1
                and s1[i - 1] == s2[j - 2]
                and s1[i - 2] == s2[j - 1]
            ):
                best_val = min(best_val, dp[i - 2][j - 2] + 1)

            dp[i][j] = best_val

    return dp[m][n]


def edit_alignment_with_transposition(
    s1: str, s2: str
) -> Tuple[int, List[Tuple[str, str, str]]]:
    """Computes the minimum edit distance and returns a canonical trace of operations

    by enforcing a deterministic tie-breaking hierarchy:
    Match -> Transposition -> Substitution -> Deletion -> Insertion.

    Trace format: list of tuples (operation, s1_segment, s2_segment)
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            best_val = min(
                dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost
            )

            if (
                i > 1
                and j > 1
                and s1[i - 1] == s2[j - 2]
                and s1[i - 2] == s2[j - 1]
            ):
                best_val = min(best_val, dp[i - 2][j - 2] + 1)

            dp[i][j] = best_val

    # Deterministic backtrace from (m, n) to (0, 0)
    i, j = m, n
    ops = []

    while i > 0 or j > 0:
        curr = dp[i][j]

        # 1. Match priority
        if (
            i > 0
            and j > 0
            and s1[i - 1] == s2[j - 1]
            and dp[i - 1][j - 1] == curr
        ):
            ops.append(("MATCH", s1[i - 1], s2[j - 1]))
            i -= 1
            j -= 1
            continue

        # 2. Transposition priority
        if (
            i > 1
            and j > 1
            and s1[i - 1] == s2[j - 2]
            and s1[i - 2] == s2[j - 1]
            and dp[i - 2][j - 2] + 1 == curr
        ):
            ops.append(("TRANSPOSE", s1[i - 2 : i], s2[j - 2 : j]))
            i -= 2
            j -= 2
            continue

        # 3. Substitution priority
        if (
            i > 0
            and j > 0
            and s1[i - 1] != s2[j - 1]
            and dp[i - 1][j - 1] + 1 == curr
        ):
            ops.append(("SUBSTITUTE", s1[i - 1], s2[j - 1]))
            i -= 1
            j -= 1
            continue

        # 4. Deletion priority
        if i > 0 and dp[i - 1][j] + 1 == curr:
            ops.append(("DELETE", s1[i - 1], ""))
            i -= 1
            continue

        # 5. Insertion priority
        if j > 0 and dp[i][j - 1] + 1 == curr:
            ops.append(("INSERT", "", s2[j - 1]))
            j -= 1
            continue

    ops.reverse()
    return dp[m][n], ops


# =====================================================================
# Verification and Test Cases
# =====================================================================

if __name__ == "__main__":
    test_cases = [
        # --- Original baseline tests ---
        ("kitten", "sitting", 3),
        ("rosettacode", "raisethysword", 8),
        ("ca", "abc", 3),
        ("ab", "ba", 1),
        ("", "abc", 3),
        ("abcdef", "abcdef", 0),
        # --- Repeated Values Cases ---
        ("aaa", "aaa", 0),  # All repeated identical: tests match over swap
        ("aa", "aa", 0),  # 2 repeated matches vs swap
        (
            "aaaa",
            "aa",
            2,
        ),  # Deletions on repeated characters (deterministic tie)
        ("aa", "aaaa", 2),  # Insertions on repeated characters
        ("aba", "bab", 2),  # Alternating repeats
        ("aaaa", "baaa", 1),  # Repeated runs with single modification
        # --- Deterministic Tie Cases ---
        (
            "ab",
            "cd",
            2,
        ),  # 2 substitutions vs 2 deletions + 2 insertions (tie for sub)
        (
            "a",
            "b",
            1,
        ),  # Substitution (cost 1) vs Delete + Insert (cost 2 -> no tie, but base)
        (
            "ab",
            "ba",
            1,
        ),  # Transposition (cost 1) vs 2 substitutions (cost 2)
        (
            "aba",
            "a",
            2,
        ),  # Multiple deletion combinations resolved deterministically
    ]

    print("Running Verification Tests:\n")
    all_passed = True
    for s1, s2, expected in test_cases:
        dist = edit_distance_with_transposition(s1, s2)
        dist_trace, trace = edit_alignment_with_transposition(s1, s2)

        passed = dist == expected and dist_trace == expected
        if not passed:
            all_passed = False

        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] dist('{s1}', '{s2}') = {dist} (expected {expected})")
        if not passed or len(s1) <= 4:
            print(f"       Trace: {trace}")

    print(
        f"\nResult: {'All tests passed successfully.' if all_passed else 'Some tests failed.'}"
    )