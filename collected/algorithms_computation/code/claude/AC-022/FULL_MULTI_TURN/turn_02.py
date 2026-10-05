from collections import deque
from typing import Dict, List


def edit_distance_with_transposition(a: str, b: str, restricted: bool = False) -> int:
    """
    Minimum number of insertions, deletions, substitutions and adjacent
    transpositions (each cost 1) turning `a` into `b`.

    restricted=False (default): unrestricted minimum (true Damerau-Levenshtein);
        a transposed pair may be edited further.
    restricted=True: optimal string alignment; each substring is edited at most once,
        using the local transition d[i-2][j-2] + 1.

    Deterministic, standard library only. Returns an int.
    """
    n, m = len(a), len(b)
    d: List[List[int]] = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j

    last_row: Dict[str, int] = {}  # last 1-based row where each char occurred in a

    for i in range(1, n + 1):
        ai = a[i - 1]
        last_match_col = 0
        for j in range(1, m + 1):
            bj = b[j - 1]
            cost = 0 if ai == bj else 1

            best = min(
                d[i - 1][j] + 1,         # deletion
                d[i][j - 1] + 1,         # insertion
                d[i - 1][j - 1] + cost,  # substitution / match
            )

            # explicit transposition transition
            if restricted:
                if i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == bj:
                    best = min(best, d[i - 2][j - 2] + 1)
            else:
                k = last_row.get(bj, 0)
                l = last_match_col
                if k > 0 and l > 0:
                    best = min(best, d[k - 1][l - 1] + (i - k - 1) + 1 + (j - l - 1))

            if cost == 0:
                last_match_col = j
            d[i][j] = best
        last_row[ai] = i

    return d[n][m]


def _bfs_reference(a: str, b: str) -> int:
    """Independent check: shortest path over single edits, including swaps anywhere."""
    if a == b:
        return 0
    alphabet = sorted(set(a) | set(b))
    cap = max(len(a), len(b)) + 2
    seen = {a}
    q = deque([(a, 0)])
    while q:
        s, dist = q.popleft()
        nxt = []
        for i in range(len(s)):
            nxt.append(s[:i] + s[i + 1:])                      # delete
            for c in alphabet:
                if c != s[i]:
                    nxt.append(s[:i] + c + s[i + 1:])          # substitute
        if len(s) < cap:
            for i in range(len(s) + 1):
                for c in alphabet:
                    nxt.append(s[:i] + c + s[i:])              # insert
        for i in range(len(s) - 1):
            nxt.append(s[:i] + s[i + 1] + s[i] + s[i + 2:])    # adjacent swap
        for t in nxt:
            if t not in seen:
                if t == b:
                    return dist + 1
                seen.add(t)
                q.append((t, dist + 1))
    raise AssertionError("unreachable")


def _self_test() -> None:
    fixed = [
        ("", "", 0, 0), ("", "abc", 3, 3), ("abc", "", 3, 3),
        ("ab", "ba", 1, 1), ("teh", "the", 1, 1),
        ("kitten", "sitting", 3, 3),
        ("ca", "abc", 2, 3),  # the diverging case: (unrestricted, restricted)
    ]
    for x, y, free, restr in fixed:
        assert edit_distance_with_transposition(x, y) == free, (x, y)
        assert edit_distance_with_transposition(x, y, restricted=True) == restr, (x, y)

    # Cross-check the default mode against brute force on all short strings.
    words = [""]
    for length in range(1, 4):
        words += [
            "".join(p) for p in __import__("itertools").product("abc", repeat=length)
        ]
    for x in words:
        for y in words:
            assert edit_distance_with_transposition(x, y) == _bfs_reference(x, y), (x, y)


if __name__ == "__main__":
    _self_test()
    print(edit_distance_with_transposition("ca", "abc"))                   # 2
    print(edit_distance_with_transposition("ca", "abc", restricted=True))  # 3
    print("All tests passed.")