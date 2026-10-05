def edit_distance(a: str, b: str) -> int:
    """Edit distance with insert, delete, substitute, and adjacent
    transposition, each costing 1 (optimal string alignment)."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    prev2 = [0] * (m + 1)            # row i-2
    prev = list(range(m + 1))        # row i-1 (row 0)

    for i in range(1, n + 1):
        curr = [i] + [0] * m         # d[i][0] = i
        ai = a[i - 1]
        for j in range(1, m + 1):
            bj = b[j - 1]
            cost = 0 if ai == bj else 1
            best = min(
                prev[j] + 1,          # deletion
                curr[j - 1] + 1,      # insertion
                prev[j - 1] + cost,   # substitution / match
            )
            # adjacent transposition
            if i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == bj:
                best = min(best, prev2[j - 2] + 1)
            curr[j] = best
        prev2, prev = prev, curr

    return prev[m]


if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("ab", "ba", 1),            # one transposition
        ("abcd", "acbd", 1),        # one transposition
        ("kitten", "sitting", 3),   # classic Levenshtein case
        ("ca", "abc", 3),           # OSA restriction
        ("teh", "the", 1),
        ("abcdef", "badcfe", 3),    # three transpositions
        ("a", "b", 1),
    ]
    for x, y, expected in tests:
        got = edit_distance(x, y)
        assert got == expected, (x, y, got, expected)
        assert got == edit_distance(y, x), "distance should be symmetric"
    print("All tests passed.")