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
        (max_score, choices)                          if return_summary is False
        (max_score, choices, operation_summary)       if return_summary is True

    Difficult cases (documented contract):
        stages is None                 -> (None, None)
        stages == []                   -> (0, [])
        any stage has no options       -> (None, None)
        no feasible assignment         -> (None, None)
        single-stage, single-option    -> handled exactly (feasible or not)

    Uses layered two-resource DP with deterministic reconstruction.
    Standard library only.
    """
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

    # --- Guard: disconnected / missing structures ---
    if stages is None:
        return _result(None, None)

    # Coerce to list to allow len() and indexing on any sequence type.
    stages = list(stages)
    S = len(stages)

    # --- Empty stage list: vacuous optimum, zero score, empty choices ---
    if S == 0:
        return _result(0, [])

    # --- Any empty stage makes the problem infeasible ---
    for opts in stages:
        if opts is None or len(opts) == 0:
            return _result(None, None)

    # --- Normalize limits (guarantee non-negative ints) ---
    B = int(budget_limit)
    M = int(memory_limit)
    if B < 0 or M < 0:
        return _result(None, None)

    NEG = float('-inf')

    # --- Layered two-resource DP ---
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

    # --- Best final score across all cells ---
    max_score = NEG
    for b in range(B + 1):
        for m in range(M + 1):
            if dp[S][b][m] > max_score:
                max_score = dp[S][b][m]
    if max_score == NEG:
        return _result(None, None)

    # --- Forward greedy reconstruction for lexicographic minimality ---
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


# ---------------------------------------------------------------------------
# Tests for the difficult cases
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = []

    def add(name, stages, B, M, expected, summary=False):
        tests.append((name, stages, B, M, expected, summary))

    # --- Smallest permitted inputs ---
    add("smallest feasible, exact fit",
        [[(0, 0, 0)]], 0, 0, (0, [0]))
    add("smallest feasible, nonzero",
        [[(1, 2, 7)]], 1, 2, (7, [0]))
    add("smallest infeasible",
        [[(1, 0, 5)]], 0, 0, (None, None))

    # --- Empty / disconnected structures ---
    add("empty stage list",
        [], 0, 0, (0, []))
    add("None stages",
        None, 0, 0, (None, None))
    add("stage with no options",
        [[(1, 0, 1)], []], 5, 5, (None, None))
    add("stage with None options",
        [[(1, 0, 1)], None], 5, 5, (None, None))

    # --- Zero limits ---
    add("zero limits, zero-cost options, tie to [0,0]",
        [[(0, 0, 3), (0, 0, 3)], [(0, 0, 4), (0, 0, 4)]],
        0, 0, (7, [0, 0]))
    add("zero limits, nonzero costs",
        [[(1, 0, 3)], [(1, 0, 4)]], 0, 0, (None, None))

    # --- Disconnected feasibility ---
    add("first stage blocks feasible second stage",
        [[(5, 0, 1)], [(1, 0, 9)]], 1, 0, (None, None))

    # --- Many-way ties ---
    add("all identical, many options, lexicographic",
        [[(0, 0, 5)] * 3, [(0, 0, 5)] * 3], 0, 0, (10, [0, 0]))

    # --- Tie where smaller index is more expensive but feasible ---
    add("smaller index costs more but still feasible",
        [[(1, 0, 10), (0, 0, 10)], [(1, 0, 10), (0, 0, 10)]],
        1, 0, (20, [0, 1]))

    # --- Exact-fit boundary ---
    add("exact fit on both resources",
        [[(1, 1, 2)], [(2, 2, 3)]], 3, 3, (5, [0, 0]))

    # --- Summary opt-in preserved alongside original tuple ---
    add("summary enabled keeps original fields",
        [[(1, 0, 5), (0, 0, 5)], [(2, 0, 5), (0, 0, 5)]],
        2, 0, (10, [0, 1]), summary=True)

    failures = 0
    for name, stages, B, M, expected, summary in tests:
        got = solve_multi_stage_allocation(
            stages, B, M, return_summary=summary
        )
        if summary:
            # Original two fields must be unchanged; summary is appended.
            core = got[:2]
            ok = (core == expected) and isinstance(got[2], dict) \
                 and "total_operations" in got[2]
            shown = (core, "summary_keys=" + ",".join(sorted(got[2].keys())))
        else:
            ok = (got == expected)
            shown = got
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{status}] {name}: got={shown} expected={expected}")

    print(f"\n{len(tests) - failures}/{len(tests)} tests passed.")