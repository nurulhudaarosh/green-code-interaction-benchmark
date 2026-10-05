from typing import Dict, Tuple, Union


def osa_distance(
    s1: str, s2: str, include_summary: bool = False
) -> Union[int, Tuple[int, Dict[str, int]]]:
    """
    Computes the edit distance using insertion, deletion, substitution,
    and adjacent transposition, each costing 1 (Optimal String Alignment distance).

    Args:
        s1: Source string.
        s2: Target string.
        include_summary: If True, returns a tuple of (distance, operation_summary).
                         If False (default), returns solely the integer distance.

    Returns:
        int if include_summary is False.
        Tuple[int, Dict[str, int]] if include_summary is True.
    """
    m, n = len(s1), len(s2)

    # Initialize DP table of size (m + 1) x (n + 1)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Base cases: cost of transforming to/from empty prefixes
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Counters for operation summary
    dp_cell_evaluations = 0
    candidate_transitions_evaluated = 0
    transposition_checks = 0
    transposition_candidates_valid = 0

    # Populate the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp_cell_evaluations += 1
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            # Standard Levenshtein transitions (3 candidate options)
            candidates = [
                dp[i - 1][j] + 1,        # Deletion
                dp[i][j - 1] + 1,        # Insertion
                dp[i - 1][j - 1] + cost  # Substitution / Match
            ]
            candidate_transitions_evaluated += 3

            # Adjacent transposition transition
            if i > 1 and j > 1:
                transposition_checks += 1
                if s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                    transposition_candidates_valid += 1
                    candidates.append(dp[i - 2][j - 2] + 1)
                    candidate_transitions_evaluated += 1

            dp[i][j] = min(candidates)

    distance = dp[m][n]

    if not include_summary:
        return distance

    operation_summary = {
        "dp_cell_evaluations": dp_cell_evaluations,
        "candidate_transitions_evaluated": candidate_transitions_evaluated,
        "transposition_checks": transposition_checks,
        "transposition_candidates_valid": transposition_candidates_valid,
    }

    return distance, operation_summary


if __name__ == "__main__":
    # Original behavior (unchanged output signature)
    dist_original = osa_distance("ca", "abc")
    print(f"Original invocation: {dist_original} (type: {type(dist_original).__name__})")

    # Feature-enabled behavior
    dist, summary = osa_distance("ca", "abc", include_summary=True)
    print(f"With feature enabled: distance={dist}")
    print("Operation Summary:")
    for k, v in summary.items():
        print(f"  - {k}: {v}")