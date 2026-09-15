import sys

def solve():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    it = iter(data)
    R = int(next(it))
    C = int(next(it))
    mat = [[0] * C for _ in range(R)]
    for i in range(R):
        for j in range(C):
            mat[i][j] = int(next(it))

    # 2D prefix sums
    pref = [[0] * (C + 1) for _ in range(R + 1)]
    for i in range(1, R + 1):
        row_sum = 0
        for j in range(1, C + 1):
            row_sum += mat[i - 1][j - 1]
            pref[i][j] = pref[i - 1][j] + row_sum

    Q = int(next(it))
    out_lines = []
    for _ in range(Q):
        r1 = int(next(it))
        c1 = int(next(it))
        r2 = int(next(it))
        c2 = int(next(it))

        # Inclusive rectangle sum via prefix table
        total = (
            pref[r2 + 1][c2 + 1]
            - pref[r1][c2 + 1]
            - pref[r2 + 1][c1]
            + pref[r1][c1]
        )

        # Direct scan for min and max
        mn = None
        mx = None
        for i in range(r1, r2 + 1):
            row = mat[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                if mn is None or v < mn:
                    mn = v
                if mx is None or v > mx:
                    mx = v

        out_lines.append(f"{total} {mn} {mx}")

    sys.stdout.write("\n".join(out_lines))

if __name__ == "__main__":
    solve()