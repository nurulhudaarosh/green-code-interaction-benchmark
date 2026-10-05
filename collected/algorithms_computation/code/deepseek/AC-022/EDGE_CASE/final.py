def damerau_levenshtein(a: str, b: str) -> int:
    """
    Edit distance with insertion, deletion, substitution, and adjacent
    transposition, each costing 1.

    Handles repeated values via explicit min over all transitions, and
    uses a fixed deterministic tie-breaking order:
        match/substitution  >  deletion  >  insertion  >  transposition
    (first minimum in that order wins).
    """
    n, m = len(a), len(b)

    # dp[i][j] = distance between a[:i] and b[:j]
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # Base cases: only insertions or only deletions available.
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost_sub = 0 if a[i - 1] == b[j - 1] else 1

            # Ordered candidates — first minimum wins (deterministic ties).
            candidates = [
                (dp[i - 1][j - 1] + cost_sub, "match_or_sub"),  # 1st
                (dp[i - 1][j] + 1,           "delete"),         # 2nd
                (dp[i][j - 1] + 1,           "insert"),         # 3rd
            ]

            # Transposition candidate (only if applicable) — 4th.
            if (i > 1 and j > 1
                    and a[i - 1] == b[j - 2]
                    and a[i - 2] == b[j - 1]):
                candidates.append((dp[i - 2][j - 2] + 1, "transpose"))

            # Pick first minimum in fixed order.
            best = min(candidates, key=lambda c: c[0])[0]
            dp[i][j] = best

    return dp[n][m]


def _run_tests():
    # (a, b, expected, label)
    tests = [
        # --- Original test suite (must be preserved) ---
        ("", "", 0, "empty/empty"),
        ("abc", "", 3, "delete all"),
        ("", "abc", 3, "insert all"),
        ("abc", "abc", 0, "identical"),
        ("abc", "abd", 1, "one substitution"),
        ("abc", "acb", 1, "one transposition"),
        ("ca", "abc", 3, "mixed"),
        ("kitten", "sitting", 3, "classic"),
        ("ab", "ba", 1, "adjacent swap"),
        ("abcd", "badc", 2, "two transpositions"),
        ("a cat", "an act", 3, "spaced phrase"),

        # --- Repeated-value cases ---
        ("aaa", "aaa", 0, "all repeats identical"),
        ("aaa", "aa", 1, "repeats, one deletion"),
        ("aa", "aaa", 1, "repeats, one insertion"),
        ("aab", "aba", 1, "repeat + transposition"),
        ("abab", "baba", 2, "alternating repeats"),
        ("aaaa", "bbbb", 4, "no shared chars, repeats"),
        ("aabb", "abab", 1, "block vs alternating"),
        ("banana", "ananas", 2, "fruit repeats"),
        ("mississippi", "misisippi", 2, "heavily repeated"),

        # --- Deterministic tie cases ---
        ("ab", "cd", 2, "sub/sub tie -> 2"),
        ("a", "b", 1, "single sub"),
        ("ab", "ba", 1, "transpose beats delete+insert"),
        ("abc", "cba", 2, "reverse 3, two transposes"),
        ("aa", "bb", 2, "both chars differ"),
        ("ax", "xa", 1, "transpose vs sub tie -> transpose wins"),
        ("abcd", "dcba", 2, "reverse 4 in two transposes"),

        # --- Symmetry checks (repeat + tie) ---
        ("aab", "baa", 1, "sym check 1"),
        ("baa", "aab", 1, "sym check 2"),
        ("abcdef", "badcfe", 3, "three disjoint swaps"),
    ]

    ok = 0
    for a, b, expected, label in tests:
        got = damerau_levenshtein(a, b)
        # Also assert symmetry for every non-trivial case.
        rev = damerau_levenshtein(b, a)
        symmetric = (got == rev)

        passed = (got == expected) and symmetric
        status = "OK  " if passed else "FAIL"
        if passed:
            ok += 1

        note = "" if symmetric else "  <-- ASYMMETRIC!"
        print(f"[{status}] {label:38s} d({a!r}, {b!r}) = {got} "
              f"(expected {expected}){note}")

    print(f"\n{ok}/{len(tests)} tests passed.")


if __name__ == "__main__":
    _run_tests()