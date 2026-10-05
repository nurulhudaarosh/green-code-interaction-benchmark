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

Optional feature (OFF by default): operation_summary
  Enabled by input key "operation_summary": true, or CLI flag
  --operation-summary, or run(data, operation_summary=True). When enabled the
  result gains one extra LAST key (also on infeasible results):
    "operation_summary": {
      "stages": n,                      # stages processed
      "dp_states": n*(B+1)*(M+1),       # DP cells filled (0 if limit < 0)
      "transitions_considered": ...,    # option evaluations during DP fill
      "transitions_applied": ...,       # of those, fit limits and next state feasible
      "best_updates": ...,              # times a cell's best value improved
      "reconstruction_checks": ...,     # options examined during reconstruction
      "total_operations": transitions_considered + reconstruction_checks }
  All counts are deterministic functions of the input. When disabled, output
  is identical to before (no extra key).

Edge cases:
  * Zero stages: feasible, score 0, choices [], cost 0, memory 0 (limits >= 0).
  * A stage with no options: infeasible. Negative limit: infeasible.
  * Stages are independent (coupled only by the global limits), so there is
    no connectivity to handle.

Input contract (enforced): limits are integers; every option is
[cost, memory, score] of integers with cost >= 0 and memory >= 0. Anything
else raises ValueError (CLI: message on stderr, exit 2).

Algorithm: layered 2-resource DP from the last stage backwards, then
deterministic forward reconstruction taking the smallest option index that
still attains the optimum.

Usage: python s.py [--operation-summary] < input.json   |   python s.py --test
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


def _solve(budget, memory, stages):
    """Return (result_or_None, stats)."""
    n = len(stages)
    stats = {"stages": n, "dp_states": 0, "transitions_considered": 0,
             "transitions_applied": 0, "best_updates": 0,
             "reconstruction_checks": 0, "total_operations": 0}
    if budget < 0 or memory < 0:
        return None, stats
    W = memory + 1
    size = (budget + 1) * W

    layers = [None] * (n + 1)
    layers[n] = [0] * size
    for i in range(n - 1, -1, -1):
        nxt = layers[i + 1]
        cur = [NEG] * size
        opts = stages[i]
        stats["dp_states"] += size
        stats["transitions_considered"] += size * len(opts)
        for b in range(budget + 1):
            row = b * W
            for m in range(W):
                best = NEG
                for c, w, s in opts:
                    if c <= b and w <= m:
                        v = nxt[(b - c) * W + (m - w)]
                        if v != NEG:
                            stats["transitions_applied"] += 1
                            if v + s > best:
                                best = v + s
                                stats["best_updates"] += 1
                cur[row + m] = best
        layers[i] = cur

    total = layers[0][budget * W + memory]
    if total == NEG:
        stats["total_operations"] = stats["transitions_considered"]
        return None, stats

    choices, b, m = [], budget, memory
    used_c = used_w = 0
    for i in range(n):
        target = layers[i][b * W + m]
        nxt = layers[i + 1]
        for j, (c, w, s) in enumerate(stages[i]):
            stats["reconstruction_checks"] += 1
            if c <= b and w <= m:
                v = nxt[(b - c) * W + (m - w)]
                if v != NEG and v + s == target:
                    choices.append(j)
                    b -= c
                    m -= w
                    used_c += c
                    used_w += w
                    break
    stats["total_operations"] = (stats["transitions_considered"]
                                 + stats["reconstruction_checks"])
    return ({"feasible": True, "score": total, "choices": choices,
             "cost": used_c, "memory": used_w}, stats)


def solve(budget, memory, stages):
    """Original API: result dict or None (unchanged behavior)."""
    return _solve(budget, memory, stages)[0]


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


def run(data, operation_summary=False):
    budget, memory, stages = validate(data)
    flag = data.get("operation_summary", False) if isinstance(data, dict) else False
    if not isinstance(flag, bool):
        raise ValueError("operation_summary must be true or false")
    res, stats = _solve(budget, memory, stages)
    out = res if res else {"feasible": False}
    if operation_summary or flag:
        out = dict(out)
        out["operation_summary"] = stats
    return out


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
                [[[0, -1, 5], [0, 0, 1]]],       # negative memory
                [[[-1, 0, 5], [0, 0, 1]]],       # negative cost
                [[[1.0, 0, 5]]],                 # float
                [[[True, 0, 5]]],                # bool
                [[[1, 1]]],                      # wrong arity
            ]
            for st in bad:
                with self.assertRaises(ValueError):
                    run({"budget": 3, "memory": 3, "stages": st})
            with self.assertRaises(ValueError):
                run({"budget": 2.7, "memory": 3, "stages": []})
            with self.assertRaises(ValueError):
                run({"budget": 1, "memory": 1})

        def test_summary_off_by_default_and_unchanged(self):
            self.assertNotIn("operation_summary", run(SAMPLE))
            self.assertNotIn("operation_summary", run(dict(SAMPLE, operation_summary=False)))
            self.assertEqual(run(SAMPLE), {"feasible": True, "score": 17,
                             "choices": [0, 1, 0], "cost": 10, "memory": 7})

        def test_summary_sample_exact_counts(self):
            r = run(SAMPLE, operation_summary=True)
            self.assertEqual(list(r)[-1], "operation_summary")
            base = dict(r)
            s = base.pop("operation_summary")
            self.assertEqual(base, run(SAMPLE))
            self.assertEqual(s["stages"], 3)
            self.assertEqual(s["dp_states"], 3 * 11 * 9)
            self.assertEqual(s["transitions_considered"], 99 * (3 + 2 + 3))
            self.assertEqual(s["reconstruction_checks"], 4)
            self.assertEqual(s["total_operations"], 792 + 4)
            self.assertEqual(r, run(dict(SAMPLE, operation_summary=True)))  # flag via input

        def test_summary_edge_cases(self):
            z = {"stages": 0, "dp_states": 0, "transitions_considered": 0,
                 "transitions_applied": 0, "best_updates": 0,
                 "reconstruction_checks": 0, "total_operations": 0}
            r = run({"budget": 0, "memory": 0, "stages": []}, operation_summary=True)
            self.assertEqual(r["operation_summary"], z)       # zero stages
            self.assertEqual(r["choices"], [])
            r = run({"budget": -1, "memory": 0, "stages": [[[0, 0, 1]]]}, operation_summary=True)
            self.assertEqual(r["feasible"], False)            # negative limit: no DP
            self.assertEqual(r["operation_summary"]["dp_states"], 0)
            r = run({"budget": 0, "memory": 0, "stages": [[[1, 0, 4]]]}, operation_summary=True)
            self.assertEqual(r["feasible"], False)            # infeasible after DP
            self.assertEqual(r["operation_summary"]["reconstruction_checks"], 0)
            self.assertEqual(r["operation_summary"]["total_operations"], 1)
            r = run({"budget": 0, "memory": 0, "stages": [[[0, 0, 4]]]}, operation_summary=True)
            self.assertEqual(r["operation_summary"]["total_operations"], 2)  # 1 DP + 1 check
            with self.assertRaises(ValueError):
                run(dict(SAMPLE, operation_summary="yes"))

        def test_summary_random_invariants(self):
            rnd = random.Random(99)
            for _ in range(300):
                n = rnd.randint(0, 4)
                B, M = rnd.randint(0, 6), rnd.randint(0, 6)
                st = [[[rnd.randint(0, 3), rnd.randint(0, 3), rnd.randint(-2, 6)]
                       for _ in range(rnd.randint(0, 3))] for _ in range(n)]
                d = {"budget": B, "memory": M, "stages": st}
                plain, withs = run(d), run(d, operation_summary=True)
                s = withs.pop("operation_summary")
                self.assertEqual(plain, withs)                # fields unchanged
                self.assertEqual(s["dp_states"], n * (B + 1) * (M + 1))
                self.assertEqual(s["transitions_considered"],
                                 sum(len(o) for o in st) * (B + 1) * (M + 1))
                self.assertLessEqual(s["transitions_applied"], s["transitions_considered"])
                self.assertEqual(s["total_operations"],
                                 s["transitions_considered"] + s["reconstruction_checks"])
                self.assertEqual(s, run(d, operation_summary=True)["operation_summary"])

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
        flag = "--operation-summary" in sys.argv[1:]
        print(json.dumps(run(json.loads(raw) if raw else SAMPLE, flag)))
    except (ValueError, json.JSONDecodeError) as ex:
        print("invalid input: %s" % ex, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()