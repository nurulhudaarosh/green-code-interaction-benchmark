from typing import Any, Dict, Union


def damerau_levenshtein_distance(
    s1: str, s2: str, include_summary: bool = False
) -> Union[int, Dict[str, Any]]:
    """Compute true Damerau-Levenshtein distance with explicit handling for

    repeated values and deterministic tie breaking among candidate operations.

    Tie-breaking precedence (lowest rank wins on cost ties):
      1. Match (cost = 0)
      2. Transposition (cost = 1)
      3. Substitution (cost = 1)
      4. Deletion (cost = 1)
      5. Insertion (cost = 1)
    """
    n, m = len(s1), len(s2)
    max_dist = n + m

    # Alphabet map for last seen indices in s1
    alphabet = set(s1) | set(s2)
    da = {ch: 0 for ch in alphabet}

    # dp table: (n + 2) x (m + 2)
    dp = [[0] * (m + 2) for _ in range(n + 2)]

    dp[0][0] = max_dist
    for i in range(0, n + 1):
        dp[i + 1][0] = max_dist
        dp[i + 1][1] = i
    for j in range(0, m + 1):
        dp[0][j + 1] = max_dist
        dp[1][j + 1] = j

    grid_evaluations = 0
    transposition_candidates_checked = 0
    transposition_selected_count = 0

    for i in range(1, n + 1):
        db = 0
        for j in range(1, m + 1):
            grid_evaluations += 1
            k = da[s2[j - 1]]
            l = db

            is_match = s1[i - 1] == s2[j - 1]
            if is_match:
                cost = 0
                db = j
            else:
                cost = 1

            candidates = []

            # 1. Match or Substitution
            sub_cost = dp[i][j] + cost
            if is_match:
                candidates.append((sub_cost, 1, "match"))
            else:
                candidates.append((sub_cost, 3, "substitution"))

            # 2. Deletion
            del_cost = dp[i][j + 1] + 1
            candidates.append((del_cost, 4, "deletion"))

            # 3. Insertion
            ins_cost = dp[i + 1][j] + 1
            candidates.append((ins_cost, 5, "insertion"))

            # 4. Transposition (if candidate characters were seen previously)
            if k > 0 and l > 0:
                transposition_candidates_checked += 1
                trans_cost = (
                    dp[k][l]
                    + (i - k - 1)
                    + (j - l - 1)
                    + 1
                )
                candidates.append((trans_cost, 2, "transposition"))

            # Deterministic selection: sort by (cost, precedence_rank)
            candidates.sort(key=lambda item: (item[0], item[1]))
            chosen_cost, _, chosen_op = candidates[0]

            if chosen_op == "transposition":
                transposition_selected_count += 1

            dp[i + 1][j + 1] = chosen_cost

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


def run_tests():
    # 1. Repeated values: all identical characters
    assert damerau_levenshtein_distance("AAAA", "AA") == 2
    assert damerau_levenshtein_distance("AAAA", "AAAA") == 0
    assert damerau_levenshtein_distance("AA", "AAAA") == 2

    # 2. Repeated alternating patterns with transpositions
    # "BABA" -> "ABAB" requires 2 transpositions (cost 2)
    assert damerau_levenshtein_distance("BABA", "ABAB") == 2

    # 3. Repeated values with interleaving insertions/deletions
    # "AABAA" -> "AAAB"
    assert damerau_levenshtein_distance("AABAA", "AAAB") == 2

    # 4. Deterministic ties:
    # "AB" -> "BA" (can be 1 transposition OR 2 substitutions; cost 1 wins)
    res_ab_ba = damerau_levenshtein_distance("AB", "BA", include_summary=True)
    assert res_ab_ba["distance"] == 1
    assert res_ab_ba["operation_summary"]["transposition_selected_count"] >= 1

    # "AC" -> "BD": Cost is 2 via 2 substitutions or 2 deletions + 2 insertions
    # Tie resolution is fully deterministic
    res_tie = damerau_levenshtein_distance("AC", "BD", include_summary=True)
    assert res_tie["distance"] == 2
    assert res_tie["operation_summary"]["grid_evaluations"] == 4

    # 5. Backward compatibility and baseline cases
    assert damerau_levenshtein_distance("CA", "ABC") == 2
    assert damerau_levenshtein_distance("", "") == 0
    assert damerau_levenshtein_distance("abc", "") == 3
    assert damerau_levenshtein_distance("", "xyz") == 3

    print("All tests passed successfully.")


if __name__ == "__main__":
    run_tests()