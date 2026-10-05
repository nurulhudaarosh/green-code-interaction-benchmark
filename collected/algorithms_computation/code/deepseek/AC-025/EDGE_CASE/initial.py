import sys

def solve():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    it = iter(data)

    S = int(next(it))
    B = int(next(it))
    M = int(next(it))

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

    # suf[i][b][m] = best score from stages i..S-1 with at most b budget, m memory
    # Use list of 2D lists.
    suf = [None] * (S + 1)

    # base layer
    base = [[0] * (M + 1) for _ in range(B + 1)]
    suf[S] = base

    for i in range(S - 1, -1, -1):
        nxt = suf[i + 1]
        cur = [[-10**18] * (M + 1) for _ in range(B + 1)]

        opts = list(zip(cost[i], mem[i], score[i]))

        for b in range(B + 1):
            cur_b = cur[b]
            for m in range(M + 1):
                best = -10**18
                for c, mm, sc in opts:
                    if c <= b and mm <= m:
                        val = sc + nxt[b - c][m - mm]
                        if val > best:
                            best = val
                cur_b[m] = best
        suf[i] = cur

    best_score = suf[0][B][M]

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
            raise RuntimeError("No valid choice found during reconstruction")
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