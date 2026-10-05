def edit_distance(s: str, t: str) -> int:
    """True Damerau-Levenshtein distance: insert, delete, substitute,
    and adjacent transposition, each with cost 1.

    Output is a single integer. Ties between equal-cost edit sequences
    cannot affect it: each cell is min() over four candidates evaluated
    in a fixed order (substitute/match, insert, delete, transpose).
    """
    n, m = len(s), len(t)
    if n == 0:
        return m
    if m == 0:
        return n

    last_row = {}  # last 1-based row in s where each character occurred

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
        last_match_col = 0
        for j in range(1, m + 1):
            i1 = last_row.get(t[j - 1], 0)
            j1 = last_match_col

            if s[i - 1] == t[j - 1]:
                cost = 0
                last_match_col = j
            else:
                cost = 1

            D[i + 1][j + 1] = min(
                D[i][j] + cost,                          # substitute / match
                D[i + 1][j] + 1,                         # insert
                D[i][j + 1] + 1,                         # delete
                D[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1),  # transpose
            )

        last_row[s[i - 1]] = i

    return D[n + 1][m + 1]


# ---------------------------------------------------------------- tests ----

def _bfs_reference(alphabet: str, max_len: int, source: str) -> dict:
    """Brute-force unrestricted edit distance from `source` to every string
    of length <= max_len over `alphabet`. Neighbours are generated in a fixed
    order, so this is deterministic too."""
    dist = {source: 0}
    frontier = [source]
    while frontier:
        nxt = []
        for cur in frontier:
            d = dist[cur] + 1
            cands = []
            for i in range(len(cur)):                       # delete
                cands.append(cur[:i] + cur[i + 1:])
            for i in range(len(cur) + 1):                   # insert
                if len(cur) < max_len:
                    for c in alphabet:
                        cands.append(cur[:i] + c + cur[i:])
            for i in range(len(cur)):                       # substitute
                for c in alphabet:
                    if c != cur[i]:
                        cands.append(cur[:i] + c + cur[i + 1:])
            for i in range(len(cur) - 1):                   # transpose
                if cur[i] != cur[i + 1]:
                    cands.append(cur[:i] + cur[i + 1] + cur[i] + cur[i + 2:])
            for c in cands:
                if c not in dist:
                    dist[c] = d
                    nxt.append(c)
        frontier = nxt
    return dist


def _all_strings(alphabet: str, max_len: int):
    out = [""]
    layer = [""]
    for _ in range(max_len):
        layer = [p + c for p in layer for c in alphabet]
        out.extend(layer)
    return out


def run_tests() -> None:
    # --- original tests (one corrected) ---
    original = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("ab", "ba", 1),
        ("abcd", "acbd", 1),
        ("kitten", "sitting", 3),
        ("ca", "abc", 2),             # true DL; OSA would give 3
        ("a", "b", 1),
        ("abcdef", "abcfed", 2),      # corrected from 3
    ]

    # --- repeated values ---
    repeated = [
        ("aa", "aa", 0),
        ("aaa", "aa", 1),
        ("aaaa", "aaa", 1),
        ("a", "aaa", 2),
        ("aab", "aba", 1),            # swap among repeated letters
        ("abab", "baba", 2),
        ("abba", "baab", 2),          # two separate swaps
        ("abcabc", "acbacb", 2),
        ("aaab", "baaa", 2),          # b is not adjacent to its target slot
        ("aaaa", "bbbb", 4),
    ]

    # --- deterministic ties (several optimal paths, one value) ---
    ties = [
        ("ab", "bc", 2),     # 2 subs  vs  delete+insert
        ("abc", "bcd", 2),   # 2 ways: delete a + insert d, or 3 subs is worse
        ("ab", "ba", 1),     # swap beats 2 substitutions
        ("abc", "cba", 2),   # several equal-cost routes
    ]

    for a, b, expected in original + repeated + ties:
        got = edit_distance(a, b)
        assert got == expected, (a, b, got, expected)
        assert edit_distance(a, b) == got            # repeat call, same result
        assert edit_distance(b, a) == got            # symmetry (ops invertible)
        print(f"OK: edit_distance({a!r}, {b!r}) = {got}")

    # --- exhaustive cross-check against brute force (heavy on repeats) ---
    for alphabet in ("ab", "abc"):
        max_len = 3
        strings = _all_strings(alphabet, max_len)
        for src in strings:
            ref = _bfs_reference(alphabet, 2 * max_len, src)
            for dst in strings:
                assert edit_distance(src, dst) == ref[dst], (src, dst)
        print(f"OK: exhaustive check over {alphabet!r}, length <= {max_len} "
              f"({len(strings) ** 2} pairs)")

    # --- invariants ---
    for x in _all_strings("ab", 4):
        assert edit_distance(x, x) == 0
        assert edit_distance(x, "") == len(x)

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()