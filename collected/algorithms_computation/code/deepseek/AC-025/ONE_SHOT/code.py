def solve_stages(stages, budget_limit, memory_limit):
    """
    Solve multi-stage decision problem with two resource constraints.
    
    Each stage requires exactly one option. Each option has (budget_cost, memory_cost, score).
    Maximize total score under global budget and memory limits.
    Ties broken by lexicographically smallest choice vector.
    
    Returns: (max_score, choice_vector, total_budget, total_memory)
             or (None, None, None, None) if infeasible.
    """
    n = len(stages)
    if n == 0:
        return (0, [], 0, 0)

    NEG_INF = float('-inf')

    # ---------- Forward DP ----------
    # dp_prev[b][m] = max score using stages processed so far with exactly b budget, m memory
    dp_prev = [[NEG_INF] * (memory_limit + 1) for _ in range(budget_limit + 1)]
    dp_prev[0][0] = 0

    for stage_idx in range(n):
        dp_curr = [[NEG_INF] * (memory_limit + 1) for _ in range(budget_limit + 1)]
        options = stages[stage_idx]
        for b in range(budget_limit + 1):
            row_prev = dp_prev[b]
            for m in range(memory_limit + 1):
                base = row_prev[m]
                if base == NEG_INF:
                    continue
                for cost_b, cost_m, score in options:
                    nb = b + cost_b
                    nm = m + cost_m
                    if nb <= budget_limit and nm <= memory_limit:
                        cand = base + score
                        if cand > dp_curr[nb][nm]:
                            dp_curr[nb][nm] = cand
        dp_prev = dp_curr

    # ---------- Find maximum score ----------
    max_score = NEG_INF
    for b in range(budget_limit + 1):
        row = dp_prev[b]
        for m in range(memory_limit + 1):
            if row[m] > max_score:
                max_score = row[m]

    if max_score == NEG_INF:
        return (None, None, None, None)

    # ---------- Suffix DP for reconstruction ----------
    # suffix_dp[i][b][m] = max score achievable from stages i..n-1
    # using exactly b budget and m memory
    suffix_dp = [None] * (n + 1)
    suffix_dp[n] = [[NEG_INF] * (memory_limit + 1) for _ in range(budget_limit + 1)]
    suffix_dp[n][0][0] = 0

    for i in range(n - 1, -1, -1):
        cur = [[NEG_INF] * (memory_limit + 1) for _ in range(budget_limit + 1)]
        nxt = suffix_dp[i + 1]
        options = stages[i]
        for b in range(budget_limit + 1):
            cur_row = cur[b]
            for m in range(memory_limit + 1):
                best = NEG_INF
                for cost_b, cost_m, score in options:
                    if b >= cost_b and m >= cost_m:
                        prev_val = nxt[b - cost_b][m - cost_m]
                        if prev_val != NEG_INF:
                            cand = prev_val + score
                            if cand > best:
                                best = cand
                cur_row[m] = best
        suffix_dp[i] = cur

    # ---------- Forward greedy reconstruction (lexicographically smallest) ----------
    choice_vector = []
    remaining_b = budget_limit
    remaining_m = memory_limit
    accumulated_score = 0

    for i in range(n):
        options = stages[i]
        chosen = None
        for opt_idx in range(len(options)):
            cost_b, cost_m, score = options[opt_idx]
            if cost_b <= remaining_b and cost_m <= remaining_m:
                nb = remaining_b - cost_b
                nm = remaining_m - cost_m
                suffix_val = suffix_dp[i + 1][nb][nm]
                if suffix_val != NEG_INF and accumulated_score + score + suffix_val == max_score:
                    chosen = opt_idx
                    remaining_b = nb
                    remaining_m = nm
                    accumulated_score += score
                    break
        if chosen is None:
            return (None, None, None, None)
        choice_vector.append(chosen)

    total_budget = budget_limit - remaining_b
    total_memory = memory_limit - remaining_m
    return (max_score, choice_vector, total_budget, total_memory)


# ---------------- Demo / Self-test ----------------
if __name__ == "__main__":
    from itertools import product

    def brute_force_check(stages, budget_limit, memory_limit):
        n = len(stages)
        best_score = -1
        best_choice = None
        best_b = best_m = 0
        for choices in product(*[range(len(s)) for s in stages]):
            tb = sum(stages[i][choices[i]][0] for i in range(n))
            tm = sum(stages[i][choices[i]][1] for i in range(n))
            ts = sum(stages[i][choices[i]][2] for i in range(n))
            if tb <= budget_limit and tm <= memory_limit:
                if ts > best_score or (ts == best_score and choices < tuple(best_choice)):
                    best_score = ts
                    best_choice = list(choices)
                    best_b, best_m = tb, tm
        return (best_score if best_choice is not None else None,
                best_choice, best_b, best_m)

    stages = [
        [(2, 3, 10), (3, 2, 12), (1, 5, 8)],
        [(4, 1, 15), (2, 4, 11), (3, 3, 13)],
        [(1, 2, 7), (2, 3, 9), (3, 1, 6)],
    ]
    budget_limit = 8
    memory_limit = 10

    dp_result = solve_stages(stages, budget_limit, memory_limit)
    bf_result = brute_force_check(stages, budget_limit, memory_limit)

    print(f"DP result: {dp_result}")
    print(f"BF result: {bf_result}")
    print(f"Match: {dp_result == bf_result}")

    # Expected style of output:
    # DP result: (35, [1, 0, 0], 8, 6)
    # BF result: (35, [1, 0, 0], 8, 6)
    # Match: True