from typing import Any, Dict, Tuple, Union


def damerau_levenshtein_distance(
    s1: str, s2: str, include_summary: bool = False
) -> Union[int, Dict[str, Any]]:
    """Compute the Damerau-Levenshtein edit distance between s1 and s2.

    Parameters:
        s1: Source string.
        s2: Target string.
        include_summary: If True, returns a dict with 'distance' and 'operation_summary'.
                         If False (default), returns the integer distance directly.
    """
    n, m = len(s1), len(s2)
    max_dist = n + m

    # Alphabet tracking for true Damerau-Levenshtein
    alphabet = set(s1) | set(s2)
    da = {ch: 0 for ch in alphabet}

    # dp table of size (n + 2) x (m + 2)
    dp = [[0] * (m + 2) for _ in range(n + 2)]

    dp[0][0] = max_dist
    for i in range(0, n + 1):
        dp[i + 1][0] = max_dist
        dp[i + 1][1] = i
    for j in range(0, m + 1):
        dp[0][j + 1] = max_dist
        dp[1][j + 1] = j

    # Operation summary metrics
    grid_evaluations = 0
    transposition_candidates_checked = 0
    transposition_selected_count = 0

    for i in range(1, n + 1):
        db = 0
        for j in range(1, m + 1):
            grid_evaluations += 1
            k = da[s2[j - 1]]
            l = db

            if s1[i - 1] == s2[j - 1]:
                cost = 0
                db = j
            else:
                cost = 1

            del_cost = dp[i][j + 1] + 1
            ins_cost = dp[i + 1][j] + 1
            sub_cost = dp[i][j] + cost

            best_val = min(del_cost, ins_cost, sub_cost)

            # Explicit transposition transition
            if k > 0 and l > 0:
                transposition_candidates_checked += 1
                trans_cost = (
                    dp[k][l]
                    + (i - k - 1)
                    + (j - l - 1)
                    + 1
                )
                if trans_cost < best_val:
                    transposition_selected_count += 1
                    best_val = trans_cost

            dp[i + 1][j + 1] = best_val

        da[s1[i - 1]] = i

    distance = dp[n + 1][m + 1]

    if not include_summary:
        return distance

    return {
        "distance": distance,
        "operation_summary": {
            "grid_evaluations": grid_evaluations,
            "transposition_candidates_checked": transposition_candidates_checked,
            "transposition_selected_count": transposition_selected_count,
        },
    }


if __name__ == "__main__":
    # 1. Default behavior remains unchanged (returns integer)
    dist = damerau_levenshtein_distance("CA", "ABC")
    assert isinstance(dist, int)
    assert dist == 2

    # 2. Enhanced behavior with operation_summary
    result = damerau_levenshtein_distance("CA", "ABC", include_summary=True)
    assert isinstance(result, dict)
    assert result["distance"] == 2
    assert result["operation_summary"]["grid_evaluations"] == 6  # 2 * 3 cells
    assert result["operation_summary"]["transposition_candidates_checked"] >= 1
    assert result["operation_summary"]["transposition_selected_count"] >= 1

    print("Result with summary:", result)