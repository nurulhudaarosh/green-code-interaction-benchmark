import os
import sys
import unittest


# ============================================================
# Solver
# ============================================================

def solve_tsp(dist, return_summary=False):
    """
    Exact TSP from city 0 using Held-Karp subset DP.

    Deterministic tie-breaking: on a cost tie, prefer the tour with the
    smaller predecessor at the latest differing position (equivalently,
    the lexicographically smaller reversed path).

    Returns:
        (cost, tour)                       if return_summary is False
        (cost, tour, operation_summary)    if return_summary is True
    """
    dp_writes = 0
    closure_comparisons = 0

    n = len(dist)

    def summary():
        return "dp_writes={};closure_comparisons={};total={}".format(
            dp_writes, closure_comparisons, dp_writes + closure_comparisons
        )

    if n == 1:
        dp_writes += 1
        result = (0, [0, 0])
        return result + (summary(),) if return_summary else result

    if n == 2:
        dp_writes += 1
        result = (dist[0][1] * 2, [0, 1, 0])
        return result + (summary(),) if return_summary else result

    size = 1 << n
    dp = [[None] * n for _ in range(size)]
    dp[1][0] = (0, (0,))
    dp_writes += 1

    for mask in range(size):
        if not (mask & 1):
            continue
        for i in range(n):
            if not (mask & (1 << i)):
                continue
            state = dp[mask][i]
            if state is None:
                continue
            cost_i, path_i = state
            for k in range(n):
                if mask & (1 << k):
                    continue
                new_mask = mask | (1 << k)
                new_cost = cost_i + dist[i][k]
                new_path = path_i + (k,)
                cur = dp[new_mask][k]
                if cur is None:
                    dp[new_mask][k] = (new_cost, new_path)
                    dp_writes += 1
                elif new_cost < cur[0]:
                    dp[new_mask][k] = (new_cost, new_path)
                    dp_writes += 1
                elif new_cost == cur[0]:
                    # Tie: prefer smaller predecessor at the latest
                    # differing position -> compare reversed paths.
                    if new_path[::-1] < cur[1][::-1]:
                        dp[new_mask][k] = (new_cost, new_path)
                        dp_writes += 1

    full_mask = size - 1
    best = None  # (total_cost, reversed_key, last_city, path)
    for i in range(1, n):
        state = dp[full_mask][i]
        if state is None:
            continue
        closure_comparisons += 1
        cost_i, path_i = state
        total = cost_i + dist[i][0]
        key = (i,) + path_i[-2::-1]
        if best is None or total < best[0]:
            best = (total, key, i, path_i)
        elif total == best[0] and key < best[1]:
            best = (total, key, i, path_i)

    if best is None:
        result = (None, None)
        return result + (summary(),) if return_summary else result

    total, _, _, path = best
    tour = list(path) + [0]
    result = (total, tour)
    return result + (summary(),) if return_summary else result


# ============================================================
# CLI
# ============================================================

def main():
    data = sys.stdin.read().split()
    if not data:
        return
    idx = 0
    n = int(data[idx]); idx += 1
    dist = []
    for _ in range(n):
        row = []
        for _ in range(n):
            row.append(int(data[idx])); idx += 1
        dist.append(row)

    want_summary = ("--summary" in sys.argv[1:]) or (os.environ.get("TSP_SUMMARY") == "1")

    if want_summary:
        cost, tour, operation_summary = solve_tsp(dist, return_summary=True)
        print(cost)
        print(' '.join(map(str, tour)))
        print(operation_summary)
    else:
        cost, tour = solve_tsp(dist, return_summary=False)
        print(cost)
        print(' '.join(map(str, tour)))


# ============================================================
# Tests for difficult cases (worst-case-like for O(2^n * n^2))
# ============================================================

def all_equal_matrix(n, w=1):
    return [[0 if i == j else w for j in range(n)] for i in range(n)]


def generic_matrix(n):
    d = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            v = ((i * 7 + j * 13) % 9) + 1
            d[i][j] = v
            d[j][i] = v
    return d


def near_equal_adversarial(n):
    d = [[0 if i == j else 1 for j in range(n)] for i in range(n)]
    d[1][2] = d[2][1] = 2
    d[3][4] = d[4][3] = 2
    d[5][6] = d[6][5] = 2
    d[1][3] = d[3][1] = 2
    return d


class TestDifficultCases(unittest.TestCase):

    # Case A: n=14, all-equal weights -> maximal ties, worst constant factor.
    def test_case_A_all_equal_14(self):
        n = 14
        dist = all_equal_matrix(n, 1)
        cost, tour = solve_tsp(dist)
        self.assertEqual(cost, n)
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)
        self.assertEqual(len(tour), n + 1)
        self.assertEqual(sorted(tour[:-1]), list(range(n)))
        self.assertEqual(tour, list(range(n)) + [0])

        cost2, tour2, s1 = solve_tsp(dist, return_summary=True)
        cost3, tour3, s2 = solve_tsp(dist, return_summary=True)
        self.assertEqual((cost2, tour2), (cost, tour))
        self.assertEqual(s1, s2)
        self.assertIn("dp_writes=", s1)
        self.assertIn("closure_comparisons=", s1)
        self.assertIn("total=", s1)

    # Case B: n=14, near-equal adversarial weights.
    def test_case_B_near_equal_14(self):
        n = 14
        dist = near_equal_adversarial(n)
        cost, tour = solve_tsp(dist)
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)
        self.assertEqual(len(tour), n + 1)
        self.assertEqual(sorted(tour[:-1]), list(range(n)))
        c = sum(dist[tour[i]][tour[i + 1]] for i in range(n))
        self.assertEqual(c, cost)

        cost2, tour2, s1 = solve_tsp(dist, return_summary=True)
        cost3, tour3, s2 = solve_tsp(dist, return_summary=True)
        self.assertEqual((cost2, tour2), (cost, tour))
        self.assertEqual(s1, s2)

    # Case C: n=14, generic distinct weights -> throughput worst case.
    def test_case_C_generic_14(self):
        n = 14
        dist = generic_matrix(n)
        cost, tour = solve_tsp(dist)
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)
        self.assertEqual(len(tour), n + 1)
        self.assertEqual(sorted(tour[:-1]), list(range(n)))
        c = sum(dist[tour[i]][tour[i + 1]] for i in range(n))
        self.assertEqual(c, cost)

        cost2, tour2, s1 = solve_tsp(dist, return_summary=True)
        cost3, tour3, s2 = solve_tsp(dist, return_summary=True)
        self.assertEqual((cost2, tour2), (cost, tour))
        self.assertEqual(s1, s2)

    # Case D: boundary small sizes with ties.
    def test_case_D_n1(self):
        cost, tour = solve_tsp([[0]])
        self.assertEqual(cost, 0)
        self.assertEqual(tour, [0, 0])

    def test_case_D_n2(self):
        cost, tour = solve_tsp([[0, 5], [5, 0]])
        self.assertEqual(cost, 10)
        self.assertEqual(tour, [0, 1, 0])

    def test_case_D_n3_ties(self):
        dist = [[0, 2, 2], [2, 0, 2], [2, 2, 0]]
        cost, tour = solve_tsp(dist)
        self.assertEqual(cost, 6)
        self.assertEqual(tour, [0, 1, 2, 0])

    def test_case_D_n4_ties(self):
        dist = [
            [0, 1, 9, 1],
            [1, 0, 1, 9],
            [9, 1, 0, 1],
            [1, 9, 1, 0],
        ]
        cost, tour = solve_tsp(dist)
        self.assertEqual(cost, 4)
        self.assertEqual(tour, [0, 1, 2, 3, 0])

    # Case E: previously-buggy matrix (inconsistent parent pointers).
    def test_case_E_bug_matrix(self):
        dist = [
            [0, 1, 1, 2],
            [1, 0, 2, 1],
            [1, 2, 0, 1],
            [2, 1, 1, 0],
        ]
        cost, tour = solve_tsp(dist)
        self.assertEqual(cost, 4)
        self.assertEqual(tour, [0, 1, 3, 2, 0])
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)
        self.assertEqual(sorted(tour[:-1]), [0, 1, 2, 3])
        c = sum(dist[tour[i]][tour[i + 1]] for i in range(4))
        self.assertEqual(c, cost)

    # Summary field shape and determinism.
    def test_operation_summary_shape_and_determinism(self):
        dist = all_equal_matrix(5, 1)
        _, _, s1 = solve_tsp(dist, return_summary=True)
        _, _, s2 = solve_tsp(dist, return_summary=True)
        self.assertEqual(s1, s2)
        parts = dict(kv.split("=") for kv in s1.split(";"))
        self.assertEqual(set(parts.keys()),
                         {"dp_writes", "closure_comparisons", "total"})
        self.assertEqual(int(parts["total"]),
                         int(parts["dp_writes"]) + int(parts["closure_comparisons"]))

    # Feature disabled => original 2-tuple API preserved.
    def test_disabled_feature_preserves_original_api(self):
        dist = all_equal_matrix(4, 1)
        out = solve_tsp(dist)
        self.assertEqual(len(out), 2)
        cost, tour = out
        self.assertEqual(cost, 4)
        self.assertEqual(tour, [0, 1, 2, 3, 0])


# ============================================================
# Entry point: run tests if invoked with --test, else CLI
# ============================================================

if __name__ == "__main__":
    if "--test" in sys.argv[1:]:
        # Strip our flag so unittest doesn't choke on it.
        sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if a != "--test"]
        unittest.main()
    else:
        main()