from typing import Dict, List


def damerau_levenshtein(a: str, b: str) -> int:
    """
    Minimum number of insertions, deletions, substitutions, and adjacent
    transpositions (each cost 1) needed to turn `a` into `b`.
    Deterministic; standard library only.
    """
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n

    # d has an extra leading row/column so indices line up with the
    # recurrence: d[i][j] = distance(a[:i], b[:j]).
    d: List[List[int]] = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j

    # last_row[c] = last row index i (1-based) processed so far where a[i-1] == c
    last_row: Dict[str, int] = {}

    for i in range(1, n + 1):
        ai = a[i - 1]
        last_match_col = 0  # last column j in this row where b[j-1] == ai

        for j in range(1, m + 1):
            bj = b[j - 1]
            k = last_row.get(bj, 0)   # last row where a[k-1] == bj
            l = last_match_col        # last col where b[l-1] == ai

            cost = 0 if ai == bj else 1
            if cost == 0:
                last_match_col = j

            best = min(
                d[i - 1][j] + 1,          # deletion
                d[i][j - 1] + 1,          # insertion
                d[i - 1][j - 1] + cost,   # substitution / match
            )

            if k > 0 and l > 0:
                # transposition: d[k-1][l-1] + deletions + 1 swap + insertions
                best = min(best, d[k - 1][l - 1] + (i - k - 1) + 1 + (j - l - 1))

            d[i][j] = best

        last_row[ai] = i

    return d[n][m]


def _self_test() -> None:
    cases = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("ab", "ba", 1),            # single adjacent transposition
        ("abcd", "acbd", 1),
        ("kitten", "sitting", 3),   # classic Levenshtein example
        ("ca", "abc", 2),           # true DL (OSA would give 3)
        ("a", "b", 1),
        ("abcdef", "badcfe", 3),    # three disjoint swaps
        ("teh", "the", 1),
    ]
    for x, y, expected in cases:
        got = damerau_levenshtein(x, y)
        assert got == expected, f"{x!r} -> {y!r}: expected {expected}, got {got}"
        assert damerau_levenshtein(y, x) == expected, "symmetry violated"


if __name__ == "__main__":
    _self_test()
    print(damerau_levenshtein("ca", "abc"))   # 2
    print(damerau_levenshtein("kitten", "sitting"))  # 3
    print("All tests passed.")