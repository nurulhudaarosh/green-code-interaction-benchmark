def edit_distance(a: str, b: str) -> int:
    """Edit distance with insert, delete, substitute, and adjacent
    transposition, each costing 1 (optimal string alignment).
    Uses three rolling rows: i-2, i-1, and i."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    prev2 = [0] * (m + 1)            # row i-2
    prev = list(range(m + 1))        # row i-1 (i = 0)

    for i in range(1, n + 1):
        cur = [i] + [0] * m          # dp[i][0] = i
        ai = a[i - 1]
        for j in range(1, m + 1):
            cost = 0 if ai == b[j - 1] else 1
            best = min(
                prev[j] + 1,          # deletion
                cur[j - 1] + 1,       # insertion
                prev[j - 1] + cost,   # match / substitution
            )
            # Explicit transposition transition
            if i >= 2 and j >= 2 and ai == b[j - 2] and a[i - 2] == b[j - 1]:
                best = min(best, prev2[j - 2] + 1)
            cur[j] = best
        prev2, prev = prev, cur

    return prev[m]


if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("ab", "ba", 1),            # one transposition
        ("abcd", "acbd", 1),        # one transposition
        ("kitten", "sitting", 3),
        ("ca", "abc", 3),           # OSA result (unrestricted DL gives 2)
        ("teh", "the", 1),
        ("abcdef", "badcfe", 3),    # three transpositions
        ("flaw", "lawn", 2),
    ]
    for x, y, expected in tests:
        got = edit_distance(x, y)
        assert got == expected, (x, y, got, expected)
        print(f"edit_distance({x!r}, {y!r}) = {got}")
    print("All tests passed.")