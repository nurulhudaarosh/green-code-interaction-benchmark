def edit_distance(a: str, b: str) -> int:
    """Edit distance with insert, delete, substitute, adjacent transpose (all cost 1).

    Optimal string alignment variant, computed by dynamic programming
    using three rolling rows for O(min(n, m)) extra space.
    """
    # Keep the shorter string as the column dimension to save memory.
    if len(b) > len(a):
        a, b = b, a  # distance is symmetric under this operation
    n, m = len(a), len(b)

    if m == 0:
        return n

    prev2 = [0] * (m + 1)          # row i-2
    prev = list(range(m + 1))      # row i-1 (row 0)
    curr = [0] * (m + 1)           # row i

    for i in range(1, n + 1):
        curr[0] = i
        ai = a[i - 1]
        for j in range(1, m + 1):
            bj = b[j - 1]
            cost = 0 if ai == bj else 1
            best = min(
                prev[j] + 1,          # deletion
                curr[j - 1] + 1,      # insertion
                prev[j - 1] + cost,   # substitution / match
            )
            # Explicit transposition transition
            if i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == bj:
                best = min(best, prev2[j - 2] + 1)
            curr[j] = best
        prev2, prev, curr = prev, curr, prev2

    return prev[m]


def _run_tests() -> None:
    cases = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("ab", "ba", 1),          # transposition
        ("abcd", "acbd", 1),      # transposition in the middle
        ("kitten", "sitting", 3),
        ("flaw", "lawn", 2),
        ("ca", "abc", 3),         # OSA result (unrestricted DL gives 2)
        ("abcdef", "badcfe", 3),  # three adjacent swaps
        ("a", "b", 1),
        ("intention", "execution", 5),
    ]
    for x, y, expected in cases:
        got = edit_distance(x, y)
        assert got == expected, (x, y, expected, got)
        assert edit_distance(y, x) == expected, ("symmetry", x, y)
    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()