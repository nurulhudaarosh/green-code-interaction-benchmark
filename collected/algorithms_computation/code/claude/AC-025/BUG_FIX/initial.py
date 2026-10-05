#!/usr/bin/env python3
"""Multiple-choice knapsack with two global resources (budget, memory).

Input (stdin, whitespace separated integers):
    n B M
    then for each of the n stages:
        k                      (number of options in the stage)
        k lines: cost mem score

Output:
    -1                         if no feasible selection exists
    otherwise:
        line 1: maximum total score
        line 2: choice vector (0-based option index per stage), space separated
Ties are broken by the lexicographically smallest choice vector.
"""
import sys

NEG = -(10 ** 18)  # marks an infeasible state


def solve(B, M, stages):
    """stages: list of lists of (cost, mem, score). Returns (score, choices) or None."""
    n = len(stages)
    # f[i][b][m] = best score using stages i..n-1 with at most b budget and m memory.
    f = [None] * (n + 1)
    f[n] = [[0] * (M + 1) for _ in range(B + 1)]
    for i in range(n - 1, -1, -1):
        nxt = f[i + 1]
        cur = [[NEG] * (M + 1) for _ in range(B + 1)]
        for c, w, s in stages[i]:
            if c > B or w > M:
                continue
            for b in range(c, B + 1):
                row, src = cur[b], nxt[b - c]
                for m in range(w, M + 1):
                    v = src[m - w]
                    if v != NEG and v + s > row[m]:
                        row[m] = v + s
        f[i] = cur

    best = f[0][B][M]
    if best == NEG:
        return None

    # Deterministic reconstruction: at each stage take the smallest option index
    # that still reaches the optimal value of the remaining subproblem.
    choices, b, m = [], B, M
    for i in range(n):
        target = f[i][b][m]
        for j, (c, w, s) in enumerate(stages[i]):
            if c <= b and w <= m:
                v = f[i + 1][b - c][m - w]
                if v != NEG and v + s == target:
                    choices.append(j)
                    b -= c
                    m -= w
                    break
        else:  # unreachable if the table is consistent
            raise RuntimeError("reconstruction failed")
    return best, choices


def main():
    data = sys.stdin.read().split()
    n, B, M = int(data[0]), int(data[1]), int(data[2])
    pos = 3
    stages = []
    for _ in range(n):
        k = int(data[pos]); pos += 1
        opts = []
        for _ in range(k):
            opts.append((int(data[pos]), int(data[pos + 1]), int(data[pos + 2])))
            pos += 3
        stages.append(opts)
    res = solve(B, M, stages)
    if res is None:
        print(-1)
    else:
        print(res[0])
        print(" ".join(map(str, res[1])))


if __name__ == "__main__":
    main()