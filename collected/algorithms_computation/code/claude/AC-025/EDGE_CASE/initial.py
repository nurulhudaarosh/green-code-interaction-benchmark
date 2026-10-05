#!/usr/bin/env python3
"""Multiple-choice, two-resource knapsack (exactly one option per stage).

Problem:
  - Each stage requires exactly one option.
  - Each option has (cost, memory, score).
  - Maximize total score s.t. total cost <= budget and total memory <= memory.
  - Ties: lexicographically smallest choice vector (0-indexed option indices).

Algorithm:
  Layered 2-resource DP built from the last stage backwards:
    layers[i][b][m] = max score of stages i..n-1 with at most b budget, m memory.
  Deterministic reconstruction going forward: at each stage take the smallest
  option index that still attains the optimum -> lexicographically smallest.

Input (JSON on stdin; built-in sample used if stdin is empty):
  {"budget": B, "memory": M, "stages": [[[cost, mem, score], ...], ...]}
Output (JSON on stdout):
  {"feasible": true, "score": S, "choices": [...], "cost": C, "memory": W}
  or {"feasible": false}
"""
import json
import sys

NEG = -(1 << 62)  # sentinel: infeasible state

SAMPLE = {
    "budget": 10,
    "memory": 8,
    "stages": [
        [[3, 2, 5], [4, 3, 7], [1, 1, 2]],
        [[2, 2, 4], [5, 4, 9]],
        [[2, 1, 3], [3, 3, 6], [2, 1, 3]],
    ],
}


def solve(budget, memory, stages):
    n = len(stages)
    W = memory + 1
    size = (budget + 1) * W

    layers = [None] * (n + 1)
    layers[n] = [0] * size
    for i in range(n - 1, -1, -1):
        nxt = layers[i + 1]
        cur = [NEG] * size
        opts = stages[i]
        for b in range(budget + 1):
            row = b * W
            for m in range(W):
                best = NEG
                for c, w, s in opts:
                    if c <= b and w <= m:
                        v = nxt[(b - c) * W + (m - w)]
                        if v != NEG and v + s > best:
                            best = v + s
                cur[row + m] = best
        layers[i] = cur

    total = layers[0][budget * W + memory]
    if total == NEG:
        return None

    choices, b, m = [], budget, memory
    used_c = used_w = 0
    for i in range(n):
        target = layers[i][b * W + m]
        nxt = layers[i + 1]
        for j, (c, w, s) in enumerate(stages[i]):
            if c <= b and w <= m:
                v = nxt[(b - c) * W + (m - w)]
                if v != NEG and v + s == target:
                    choices.append(j)
                    b -= c
                    m -= w
                    used_c += c
                    used_w += w
                    break
    return {"feasible": True, "score": total, "choices": choices,
            "cost": used_c, "memory": used_w}


def main():
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    data = json.loads(raw) if raw else SAMPLE
    res = solve(int(data["budget"]), int(data["memory"]), data["stages"])
    print(json.dumps(res if res else {"feasible": False}))


if __name__ == "__main__":
    main()