#!/usr/bin/env python3
"""Multi-Stage Resource Allocation (multiple-choice, two-resource knapsack).

Problem:
  n stages; each stage must select EXACTLY ONE of its options. Each option
  has (cost, memory, score). Maximize total score subject to
      sum(cost) <= budget   and   sum(memory) <= memory_limit.
  Ties between equal-score optima: lexicographically smallest choice vector
  (0-indexed option per stage, compared stage 0 first).

Output:
  {"feasible": true, "score": S, "choices": [...], "cost": C, "memory": W}
  or {"feasible": false}

Edge cases:
  * Zero stages: feasible, score 0, choices [], cost 0, memory 0 (limits >= 0).
  * A stage with no options: infeasible. Negative limit: infeasible.
  * Stages are independent (coupled only by the global limits), so there is
    no connectivity to handle.

Input contract (enforced): limits are integers; every option is
[cost, memory, score] of integers with cost >= 0 and memory >= 0. Anything
else raises ValueError (CLI: message on stderr, exit 2) instead of crashing
with IndexError/TypeError or silently misreading the DP table.

Algorithm: layered 2-resource DP from the last stage backwards, then
deterministic forward reconstruction taking the smallest option index that
still attains the optimum.

Usage: python s.py < input.json     |     python s.py --test
Input JSON: {"budget": B, "memory": M, "stages": [[[cost, mem, score], ...], ...]}
Empty stdin runs a built-in sample.
"""
import json
import sys

NEG = -(1 << 62)

SAMPLE = {
    "budget": 10, "memory": 8,
    "stages": [
        [[3, 2, 5], [4, 3, 7], [1, 1, 2]],
        [[2, 2, 4], [5, 4, 9]],
        [[2, 1, 3], [3, 3, 6], [2, 1, 3]],
    ],
}


def solve(budget, memory, stages):
    if budget < 0 or memory < 0:
        return None
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


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def validate(data):
    """Return (budget, memory, stages) or raise ValueError."""
    try:
        budget, memory, stages = data["budget"], data["memory"], data["stages"]
    except (KeyError, TypeError):
        raise ValueError("input must be an object with budget, memory, stages")
    if not _is_int(budget) or not _is_int(memory):
        raise ValueError("budget and memory must be integers")
    if not isinstance(stages, (list, tuple)):
        raise ValueError("stages must be a list")
    for i, opts in enumerate(stages):
        if not isinstance(opts, (list, tuple)):
            raise ValueError("stage %d must be a list of options" % i)
        for j, o in enumerate(opts):
            if not isinstance(o, (list, tuple)) or len(o) != 3 \
                    or not all(_is_int(v) for v in o):
                raise ValueError("stage %d option %d must be [cost, memory, score] integers" % (i, j))
            if o[0] < 0 or o[1] < 0:
                raise ValueError("stage %d option %d: cost and memory must be >= 0" % (i, j))
    return budget, memory, stages


def run(data):
    res = solve(*validate(data))
    return res if res else {"feasible": False}


def _tests():
    import itertools
    import random
    import unittest

    def brute(B, M, st):
        best = None
        for ch in itertools.product(*[range(len(s)) for s in st]):
            c = sum(st[i][j][0] for i, j in enumerate(ch))
            w = sum(st[i][j][1] for i, j in enumerate(ch))
            s = sum(st[i][j][2] for i, j in enumerate(ch))
            if c <= B and w <= M and (best is None or s > best[0]):
                best = (s, list(ch))  # product order => first max is lex-smallest
        return best

    class T(unittest.TestCase):
        def test_zero_stages(self):
            self.assertEqual(run({"budget": 0, "memory": 0, "stages": []}),
                             {"feasible": True, "score": 0, "choices": [],
                              "cost": 0, "memory": 0})
            self.assertEqual(run({"budget": 5, "memory": 7, "stages": []})["score"], 0)

        def test_zero_stages_negative_limit(self):
            self.assertEqual(run({"budget": -1, "memory": 0, "stages": []}),
                             {"feasible": False})

        def test_smallest_nonempty(self):
            self.assertEqual(run({"budget": 0, "memory": 0, "stages": [[[0, 0, 4]]]}),
                             {"feasible": True, "score": 4, "choices": [0],
                              "cost": 0, "memory": 0})

        def test_smallest_infeasible(self):
            self.assertEqual(run({"budget": 0, "memory": 0, "stages": [[[1, 0, 4]]]}),
                             {"feasible": False})

        def test_empty_option_list(self):
            self.assertEqual(run({"budget": 9, "memory": 9, "stages": [[[1, 1, 1]], []]}),
                             {"feasible": False})

        def test_single_empty_stage(self):
            self.assertEqual(run({"budget": 0, "memory": 0, "stages": [[]]}),
                             {"feasible": False})

        def test_zero_limits_zero_cost_options(self):
            r = run({"budget": 0, "memory": 0,
                     "stages": [[[0, 0, 1], [0, 0, 5]], [[0, 0, 2]]]})
            self.assertEqual((r["score"], r["choices"]), (7, [1, 0]))

        def test_negative_scores_forced(self):
            r = run({"budget": 3, "memory": 3,
                     "stages": [[[1, 1, -5], [2, 2, -2]], [[1, 1, -1]]]})
            self.assertEqual((r["score"], r["choices"]), (-3, [1, 0]))

        def test_tie_lexicographic(self):
            r = run({"budget": 4, "memory": 4,
                     "stages": [[[1, 1, 3], [2, 2, 3]], [[1, 1, 3], [2, 2, 3]]]})
            self.assertEqual(r["choices"], [0, 0])
            r = run({"budget": 3, "memory": 3,
                     "stages": [[[1, 1, 5], [2, 2, 5]], [[2, 2, 1], [1, 1, 1]]]})
            self.assertEqual(r["choices"], [0, 0])

        def test_invalid_options_rejected_not_crashing(self):
            bad = [
                [[[0, -1, 5], [0, 0, 1]]],       # negative memory (was IndexError)
                [[[-1, 0, 5], [0, 0, 1]]],       # negative cost   (was IndexError)
                [[[1.0, 0, 5]]],                 # float           (was TypeError)
                [[[True, 0, 5]]],                # bool
                [[[1, 1]]],                      # wrong arity
            ]
            for st in bad:
                with self.assertRaises(ValueError):
                    run({"budget": 3, "memory": 3, "stages": st})
            with self.assertRaises(ValueError):
                run({"budget": 2.7, "memory": 3, "stages": []})   # was silently 2
            with self.assertRaises(ValueError):
                run({"budget": 1, "memory": 1})

        def test_sample(self):
            self.assertEqual(run(SAMPLE),
                             {"feasible": True, "score": 17, "choices": [0, 1, 0],
                              "cost": 10, "memory": 7})

        def test_random_vs_bruteforce(self):
            rnd = random.Random(12345)
            for _ in range(400):
                n = rnd.randint(0, 4)
                B, M = rnd.randint(0, 8), rnd.randint(0, 8)
                st = [[[rnd.randint(0, 4), rnd.randint(0, 4), rnd.randint(-3, 8)]
                       for _ in range(rnd.randint(0, 3))] for _ in range(n)]
                exp = brute(B, M, st)
                got = run({"budget": B, "memory": M, "stages": st})
                if exp is None:
                    self.assertEqual(got, {"feasible": False})
                else:
                    self.assertEqual((got["score"], got["choices"]), exp)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(T)
    ok = unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful()
    sys.exit(0 if ok else 1)


def main():
    if "--test" in sys.argv[1:]:
        _tests()
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    try:
        print(json.dumps(run(json.loads(raw) if raw else SAMPLE)))
    except (ValueError, json.JSONDecodeError) as ex:
        print("invalid input: %s" % ex, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()