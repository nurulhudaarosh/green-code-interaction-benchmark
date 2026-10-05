def edit_distance(s: str, t: str) -> int:
    """True Damerau-Levenshtein distance: insert, delete, substitute,
    and adjacent transposition, each with cost 1."""
    n, m = len(s), len(t)
    if n == 0:
        return m
    if m == 0:
        return n

    # last_row[c] = last row index (1-based) in s where character c occurred
    last_row = {}

    # d has an extra border row/column to simplify the transposition lookup.
    # Use offset 1: D[i+1][j+1] corresponds to distance(s[:i], t[:j]).
    INF = n + m
    D = [[0] * (m + 2) for _ in range(n + 2)]
    D[0][0] = INF
    for i in range(n + 1):
        D[i + 1][0] = INF
        D[i + 1][1] = i
    for j in range(m + 1):
        D[0][j + 1] = INF
        D[1][j + 1] = j

    for i in range(1, n + 1):
        last_match_col = 0  # last column j in t where s[i-1] == t[j-1]
        for j in range(1, m + 1):
            i1 = last_row.get(t[j - 1], 0)
            j1 = last_match_col

            if s[i - 1] == t[j - 1]:
                cost = 0
                last_match_col = j
            else:
                cost = 1

            D[i + 1][j + 1] = min(
                D[i][j] + cost,          # substitution / match
                D[i + 1][j] + 1,         # insertion
                D[i][j + 1] + 1,         # deletion
                # transposition (with optional in-between deletions/insertions)
                D[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1),
            )

        last_row[s[i - 1]] = i

    return D[n + 1][m + 1]


if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("ab", "ba", 1),          # one transposition
        ("abcd", "acbd", 1),      # adjacent swap
        ("kitten", "sitting", 3), # classic Levenshtein case
        ("ca", "abc", 2),         # true DL (OSA would give 3)
        ("a", "b", 1),
        ("abcdef", "abcfed", 3),
    ]
    for a, b, expected in tests:
        got = edit_distance(a, b)
        status = "OK" if got == expected else "FAIL"
        print(f"{status}: edit_distance({a!r}, {b!r}) = {got} (expected {expected})")
        assert got == expected