import sys

NEG_INF = -10**18
INFEASIBLE = "INFEASIBLE"

def solve():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    it = iter(data)

    S = int(next(it))
    B = int(next(it))
    M = int(next(it))

    # Case: smallest permitted input (no stages)
    if S == 0:
        # Empty choice vector, zero score, zero usage
        print(0)
        print("")          # empty choice line
        print(0, 0)
        return

    cost = []
    mem = []
    score = []

    for _ in range(S):
        n = int(next(it))
        c_row = []
        m_row = []
        s_row = []
        for _ in range(n):
            c = int(next(it))
            m = int(next(it))
            sc = int(next(it))
            c_row.append(c)
            m_row.append(m)
            s_row.append(sc)
        cost.append(c_row)
        mem.append(m_row)
        score.append(s_row)

    # Case: empty / disconnected structure -> any stage with no options is infeasible
    for i in range(S):
        if len(cost[i]) == 0:
            print(INFEASIBLE)
            print(-1)
            print(-1, -1)
            return

    # Suffix DP: suf[i][b][m] = best score from stages i..S-1
    suf = [None] * (S + 1)
    suf[S] = [[0] * (M + 1) for _ in range(B + 1)]

    for i in range(S - 1, -1, -1):
        nxt = suf[i + 1]
        cur = [[NEG_INF] * (M + 1) for _ in range(B + 1)]
        opts = list(zip(cost[i], mem[i], score[i]))

        for b in range(B + 1):
            cur_b = cur[b]
            for m in range(M + 1):
                best = NEG_INF
                for c, mm, sc in opts:
                    if c <= b and mm <= m:
                        val = sc + nxt[b - c][m - mm]
                        if val > best:
                            best = val
                cur_b[m] = best
        suf[i] = cur

    best_score = suf[0][B][M]

    # Case: no feasible assignment exists
    if best_score == NEG_INF:
        print(INFEASIBLE)
        print(-1)
        print(-1, -1)
        return

    # Deterministic lexicographically smallest reconstruction
    rem_b = B
    rem_m = M
    choices = []

    for i in range(S):
        chosen = -1
        for j, (c, mm, sc) in enumerate(zip(cost[i], mem[i], score[i])):
            if c <= rem_b and mm <= rem_m:
                if sc + suf[i + 1][rem_b - c][rem_m - mm] == suf[i][rem_b][rem_m]:
                    chosen = j
                    break
        if chosen == -1:
            # Should not happen if best_score is feasible, but guard anyway
            print(INFEASIBLE)
            print(-1)
            print(-1, -1)
            return
        choices.append(chosen)
        rem_b -= cost[i][chosen]
        rem_m -= mem[i][chosen]

    used_b = B - rem_b
    used_m = M - rem_m

    print(best_score)
    print(" ".join(map(str, choices)))
    print(used_b, used_m)

if __name__ == "__main__":
    solve()