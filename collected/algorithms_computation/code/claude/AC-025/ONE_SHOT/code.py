import sys

def solve(B, M, stages):
    n = len(stages)
    layers = [None] * (n + 1)
    layers[n] = [[0] * (M + 1) for _ in range(B + 1)]

    # Backward DP over stages
    for i in range(n - 1, -1, -1):
        nxt = layers[i + 1]
        cur = [[None] * (M + 1) for _ in range(B + 1)]
        opts = stages[i]
        for b in range(B + 1):
            row = cur[b]
            for m in range(M + 1):
                best = None
                for c, w, s in opts:
                    if c <= b and w <= m:
                        v = nxt[b - c][m - w]
                        if v is not None:
                            v += s
                            if best is None or v > best:
                                best = v
                row[m] = best
        layers[i] = cur

    total = layers[0][B][M]
    if total is None:
        return None

    # Deterministic reconstruction: smallest option index achieving the optimum
    choice = []
    b, m = B, M
    for i in range(n):
        target = layers[i][b][m]
        nxt = layers[i + 1]
        for j, (c, w, s) in enumerate(stages[i]):
            if c <= b and w <= m:
                v = nxt[b - c][m - w]
                if v is not None and v + s == target:
                    choice.append(j)
                    b -= c
                    m -= w
                    break
    return total, choice


def main():
    data = sys.stdin.read().split()
    pos = 0
    n, B, M = int(data[0]), int(data[1]), int(data[2])
    pos = 3
    stages = []
    for _ in range(n):
        k = int(data[pos]); pos += 1
        opts = []
        for _ in range(k):
            c, w, s = int(data[pos]), int(data[pos + 1]), int(data[pos + 2])
            pos += 3
            opts.append((c, w, s))
        stages.append(opts)

    res = solve(B, M, stages)
    if res is None:
        print("INFEASIBLE")
    else:
        total, choice = res
        print(total)
        print(*choice)


if __name__ == "__main__":
    main()