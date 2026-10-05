from typing import Dict, Union


def edit_distance(
    a: str, b: str, summarize: bool = False
) -> Union[int, Dict[str, object]]:
    """Edit distance with insert, delete, substitute, and adjacent
    transposition (each cost 1; optimal string alignment).

    Returns an int when summarize is False (original behavior).
    When summarize is True, returns
        {"distance": int, "operation_summary": {...}}.
    """
    n, m = len(a), len(b)

    cells = candidates = eligible = improvements = 0

    if n == 0 or m == 0:
        dist = m if n == 0 else n
    else:
        prev2 = [0] * (m + 1)        # row i-2
        prev = list(range(m + 1))    # row i-1 (row 0)

        for i in range(1, n + 1):
            curr = [i] + [0] * m     # d[i][0] = i
            ai = a[i - 1]
            for j in range(1, m + 1):
                bj = b[j - 1]
                cost = 0 if ai == bj else 1
                best = min(
                    prev[j] + 1,          # deletion
                    curr[j - 1] + 1,      # insertion
                    prev[j - 1] + cost,   # substitution / match
                )
                cells += 1
                candidates += 3
                if i > 1 and j > 1 and ai == b[j - 2] and a[i - 2] == bj:
                    eligible += 1
                    candidates += 1
                    t = prev2[j - 2] + 1  # transposition
                    if t < best:
                        improvements += 1
                        best = t
                curr[j] = best
            prev2, prev = prev, curr
        dist = prev[m]

    if not summarize:
        return dist

    return {
        "distance": dist,
        "operation_summary": {
            "cells_evaluated": cells,
            "candidate_evaluations": candidates,
            "transposition_eligible": eligible,
            "transposition_improvements": improvements,
            "total_decisions": cells,
        },
    }


if __name__ == "__main__":
    tests = [
        ("", "", 0), ("", "abc", 3), ("abc", "", 3), ("abc", "abc", 0),
        ("ab", "ba", 1), ("abcd", "acbd", 1), ("kitten", "sitting", 3),
        ("ca", "abc", 3), ("teh", "the", 1), ("abcdef", "badcfe", 3),
        ("a", "b", 1),
    ]
    for x, y, expected in tests:
        # Original contract: plain int when the feature is off.
        got = edit_distance(x, y)
        assert isinstance(got, int) and got == expected, (x, y, got)
        assert got == edit_distance(y, x)

        # Feature on: same distance, plus a deterministic summary.
        r = edit_distance(x, y, summarize=True)
        assert r["distance"] == expected
        assert r == edit_distance(x, y, summarize=True)  # deterministic
        s = r["operation_summary"]
        assert s["cells_evaluated"] == len(x) * len(y)
        assert s["candidate_evaluations"] == 3 * s["cells_evaluated"] + s["transposition_eligible"]
        assert s["transposition_improvements"] <= s["transposition_eligible"]

    # Hand-verified example: "ab" -> "ba"
    assert edit_distance("ab", "ba", summarize=True) == {
        "distance": 1,
        "operation_summary": {
            "cells_evaluated": 4,
            "candidate_evaluations": 13,
            "transposition_eligible": 1,
            "transposition_improvements": 1,
            "total_decisions": 4,
        },
    }
    print("All tests passed.")