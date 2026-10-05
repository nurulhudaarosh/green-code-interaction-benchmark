def solve_multi_stage_allocation(stages, budget_limit, memory_limit,
                                 return_summary=False):
    """
    Multi-stage, two-resource (budget, memory) allocation.

    Each stage requires exactly one option. Each option is a tuple
    (budget_cost, memory_cost, score). Maximize total score subject to
    total budget <= budget_limit and total memory <= memory_limit.
    Ties on max score are broken by the lexicographically smallest
    choice vector (option indices compared stage 0 first).

    Returns:
        (max_score, choices)                                  if return_summary is False
        (max_score, choices, operation_summary)               if return_summary is True

    operation_summary is a deterministic dict reporting counts of major
    computational decisions/operations (see below).

    Uses layered two-resource DP with deterministic reconstruction.
    Standard library only.
    """
    # --- deterministic operation counters ---
    dp_states_visited = 0
    transitions_evaluated = 0
    transitions_applied = 0
    reconstruction_steps = 0

    def _summary():
        return {
            "dp_states_visited": dp_states_visited,
            "transitions_evaluated": transitions_evaluated,
            "transitions_applied": transitions_applied,
            "reconstruction_steps": reconstruction_steps,
            "total_operations": (dp_states_visited
                                 + transitions_evaluated
                                 + transitions_applied
                                 + reconstruction_steps),
        }

    def _result(max_score, choices):
        if return_summary:
            return max_score, choices, _summary()
        return max_score, choices

    # --- input validation (unchanged behavior) ---
    if stages is None:
        return _result(None, None)
    S = len(stages)
    if S == 0:
        return _result(0, [])
    for opts in stages:
        if not opts:
            return _result(None, None)

    NEG = float('-inf')
    B, M = budget_limit, memory_limit

    # --- layered two-resource DP ---
    # dp[s][b][m] = best score using first s stages with exactly b budget, m memory
    dp = [[[NEG] * (M + 1) for _ in range(B + 1)] for _ in range(S + 1)]
    dp[0][0][0] = 0

    for s in range(S):
        cur = dp[s]
        nxt = dp[s + 1]
        options = stages[s]
        for b in range(B + 1):
            row = cur[b]
            for m in range(M + 1):
                base = row[m]
                if base == NEG:
                    continue
                dp_states_visited += 1
                for (cb, cm, cs) in options:
                    transitions_evaluated += 1
                    nb, nm = b + cb, m + cm
                    if nb <= B and nm <= M:
                        v = base + cs
                        if v > nxt[nb][nm]:
                            nxt[nb][nm] = v
                            transitions_applied += 1

    # --- best final score ---
    max_score = NEG
    for b in range(B + 1):
        for m in range(M + 1):
            if dp[S][b][m] > max_score:
                max_score = dp[S][b][m]
    if max_score == NEG:
        return _result(None, None)

    # --- forward greedy reconstruction for lexicographic minimality ---
    choices = []
    b_used, m_used = 0, 0
    need = max_score
    for s in range(S):
        remaining_stages = S - s - 1
        chosen = None
        for idx, (cb, cm, cs) in enumerate(stages[s]):
            reconstruction_steps += 1
            nb, nm = b_used + cb, m_used + cm
            if nb > B or nm > M:
                continue
            target_rem = need - cs
            if target_rem < 0:
                continue
            if remaining_stages == 0:
                if dp[S][nb][nm] == max_score:
                    chosen = (idx, nb, nm, cs)
                    break
            else:
                if dp[remaining_stages][nb][nm] == target_rem:
                    chosen = (idx, nb, nm, cs)
                    break
        if chosen is None:
            return _result(None, None)
        idx, b_used, m_used, cs = chosen
        choices.append(idx)
        need -= cs

    return _result(max_score, choices)


if __name__ == "__main__":
    stages = [
        [(1, 0, 5), (0, 0, 5)],
        [(2, 0, 5), (0, 0, 5)],
    ]

    # Original 2-tuple behavior preserved (default).
    print(solve_multi_stage_allocation(stages, 2, 0))
    # -> (10, [0, 1])

    # New opt-in 3-tuple with operation_summary.
    score, choices, summary = solve_multi_stage_allocation(
        stages, 2, 0, return_summary=True
    )
    print(score, choices)
    print(summary)
    # -> 10 [0, 1]
    # -> {'dp_states_visited': ..., 'transitions_evaluated': ...,
    #     'transitions_applied': ..., 'reconstruction_steps': ...,
    #     'total_operations': ...}

    # Infeasible: summary still returned, counters reflect work done.
    print(solve_multi_stage_allocation(
        [[(10, 10, 100)], [(10, 10, 100)]], 5, 5, return_summary=True
    ))
    # -> (None, None, {...counters...})