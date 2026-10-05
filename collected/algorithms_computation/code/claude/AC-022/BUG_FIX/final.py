def edit_distance(a: str, b: str) -> int:
    """Minimum number of insertions, deletions, substitutions, and adjacent
    transpositions (each cost 1) needed to turn a into b.
    Unrestricted Damerau-Levenshtein; O(len(a) * len(b)) time and space."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    last_row = {}  # char -> last row i (1-based) where it appeared in a

    for i in range(1, n + 1):
        last_col = 0  # last column j where b[j-1] == a[i-1] in this row
        for j in range(1, m + 1):
            i1 = last_row.get(b[j - 1], 0)
            j1 = last_col
            if a[i - 1] == b[j - 1]:
                cost = 0
                last_col = j
            else:
                cost = 1

            best = min(
                dp[i - 1][j] + 1,         # deletion
                dp[i][j - 1] + 1,         # insertion
                dp[i - 1][j - 1] + cost,  # match / substitution
            )
            # Explicit transposition transition (allows edits between the pair)
            if i1 > 0 and j1 > 0:
                best = min(
                    best,
                    dp[i1 - 1][j1 - 1] + (i - i1 - 1) + 1 + (j - j1 - 1),
                )
            dp[i][j] = best
        last_row[a[i - 1]] = i

    return dp[n][m]


def _bfs_reference(source, alphabet, max_len):
    """Brute-force reference: BFS over all strings reachable by single edits."""
    dist = {source: 0}
    frontier = [source]
    while frontier:
        nxt = []
        for s in frontier:
            d = dist[s] + 1
            cands = []
            for k in range(len(s)):
                cands.append(s[:k] + s[k + 1:])                       # delete
                for c in alphabet:
                    if c != s[k]:
                        cands.append(s[:k] + c + s[k + 1:])           # substitute
                if k + 1 < len(s) and s[k] != s[k + 1]:
                    cands.append(s[:k] + s[k + 1] + s[k] + s[k + 2:])  # transpose
            if len(s) < max_len:
                for k in range(len(s) + 1):
                    for c in alphabet:
                        cands.append(s[:k] + c + s[k:])               # insert
            for t in cands:
                if t not in dist:
                    dist[t] = d
                    nxt.append(t)
        frontier = nxt
    return dist


if __name__ == "__main__":
    tests = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("ab", "ba", 1),
        ("abcd", "acbd", 1),
        ("kitten", "sitting", 3),
        ("ca", "abc", 2),            # was 3 in the buggy OSA version
        ("teh", "the", 1),
        ("abcdef", "badcfe", 3),
        ("flaw", "lawn", 2),
    ]
    for x, y, expected in tests:
        got = edit_distance(x, y)
        assert got == expected, (x, y, got, expected)
        print(f"edit_distance({x!r}, {y!r}) = {got}")

    # Exhaustive cross-check against brute force on all short strings.
    from itertools import product
    alphabet = "abc"
    strings = [""] + ["".join(p) for L in range(1, 4)
                      for p in product(alphabet, repeat=L)]
    for s in strings:
        ref = _bfs_reference(s, alphabet, max_len=4)
        for t in strings:
            assert edit_distance(s, t) == ref[t], (s, t)
    print("All tests passed (including exhaustive brute-force check).")