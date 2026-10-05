import sys

def solve(stages, budget_limit, memory_limit):
    n = len(stages)
    NEG = float('-inf')

    # dp[b][m] = (score, choice_tuple)  -- best for stages 0..i-1 reaching (b,m)
    # choice_tuple has length = number of stages processed so far.
    dp = [[None] * (memory_limit + 1) for _ in range(budget_limit + 1)]
    dp[0][0] = (0, ())

    for i in range(n):
        new_dp = [[None] * (memory_limit + 1) for _ in range(budget_limit + 1)]
        options = stages[i]
        for b in range(budget_limit + 1):
            for m in range(memory_limit + 1):
                state = dp[b][m]
                if state is None:
                    continue
                cur_score, cur_choice = state
                for j, (c, mem, s) in enumerate(options):
                    nb, nm = b + c, m + mem
                    if nb > budget_limit or nm > memory_limit:
                        continue
                    cand_score = cur_score + s
                    cand_choice = cur_choice + (j,)
                    existing = new_dp[nb][nm]
                    if existing is None:
                        new_dp[nb][nm] = (cand_score, cand_choice)
                    else:
                        e_score, e_choice = existing
                        # Maximize score; tie -> lexicographically smallest choice
                        if cand_score > e_score or (
                            cand_score == e_score and cand_choice < e_choice
                        ):
                            new_dp[nb][nm] = (cand_score, cand_choice)
        dp = new_dp

    # Scan all final states for best (score, then lexicographic choice)
    best = None
    for b in range(budget_limit + 1):
        for m in range(memory_limit + 1):
            state = dp[b][m]
            if state is None:
                continue
            if best is None:
                best = state
            else:
                bs, bc = best
                cs, cc = state
                if cs > bs or (cs == bs and cc < bc):
                    best = state

    if best is None:
        return None
    return list(best[1])


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    idx = 0
    n = int(data[idx]); idx += 1
    budget_limit = int(data[idx]); idx += 1
    memory_limit = int(data[idx]); idx += 1

    stages = []
    for _ in range(n):
        k = int(data[idx]); idx += 1
        opts = []
        for _ in range(k):
            c = int(data[idx]); idx += 1
            mem = int(data[idx]); idx += 1
            s = int(data[idx]); idx += 1
            opts.append((c, mem, s))
        stages.append(opts)

    result = solve(stages, budget_limit, memory_limit)
    if result is None:
        print("NO SOLUTION")
    else:
        print(' '.join(map(str, result)))


if __name__ == "__main__":
    main()