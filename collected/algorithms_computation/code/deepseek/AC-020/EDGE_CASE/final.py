import sys


def solve_tsp(distance_matrix):
    """
    Held-Karp TSP solver with deterministic tie-breaking.

    Tie-breaking rules:
      1) When two transitions reach the same (mask, j) state at equal cost,
         keep the smaller predecessor i.
      2) When two final cities i != 0 give the same total cost,
         pick the smaller i.

    Args:
        distance_matrix: n x n symmetric distance matrix (list of lists of ints)

    Returns:
        (min_cost: int, tour: list[int]) with tour[0] == tour[-1] == 0
    """
    n = len(distance_matrix)

    # ---- Edge cases ---------------------------------------------------
    if n == 1:
        return 0, [0, 0]
    if n == 2:
        cost = distance_matrix[0][1] + distance_matrix[1][0]
        return cost, [0, 1, 0]

    # ---- Held-Karp DP -------------------------------------------------
    full_mask = (1 << n) - 1
    INF = float('inf')

    # dp[mask][i] = min cost to start at 0, visit exactly 'mask', end at i
    # Only masks containing bit 0 are meaningful.
    dp = [[INF] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]

    dp[1][0] = 0  # start: only city 0 visited, currently at 0

    # Iterate masks in increasing numeric order.
    # Because new_mask = mask | (1 << j) > mask whenever j not in mask,
    # increasing mask order guarantees dp[mask][*] is finalized before use.
    for mask in range(1 << n):
        if not (mask & 1):
            continue  # must contain city 0

        # Snapshot row for speed (local binding)
        dp_mask = dp[mask]

        for i in range(n):
            if not (mask & (1 << i)):
                continue
            cur = dp_mask[i]
            if cur == INF:
                continue

            dist_i = distance_matrix[i]
            for j in range(n):
                if mask & (1 << j):
                    continue
                new_mask = mask | (1 << j)
                new_cost = cur + dist_i[j]

                prev_best = dp[new_mask][j]
                if new_cost < prev_best:
                    dp[new_mask][j] = new_cost
                    parent[new_mask][j] = i
                elif new_cost == prev_best:
                    # Tie: prefer smaller predecessor
                    if parent[new_mask][j] == -1 or i < parent[new_mask][j]:
                        parent[new_mask][j] = i

    # ---- Choose final city (return edge to 0) -------------------------
    min_cost = INF
    best_last = -1

    dp_full = dp[full_mask]
    for i in range(1, n):
        if dp_full[i] == INF:
            continue
        total = dp_full[i] + distance_matrix[i][0]
        if total < min_cost:
            min_cost = total
            best_last = i
        elif total == min_cost:
            # Tie: prefer smaller last city (== smaller predecessor of 0)
            if best_last == -1 or i < best_last:
                best_last = i

    if best_last == -1:
        # Should not happen for a complete graph, but be explicit.
        raise ValueError("No Hamiltonian cycle found (graph incomplete?)")

    # ---- Reconstruct tour --------------------------------------------
    tour = []
    mask = full_mask
    current = best_last
    while current != -1:
        tour.append(current)
        prev = parent[mask][current]
        mask ^= (1 << current)
        current = prev
    tour.reverse()
    tour.append(0)  # close the cycle

    return min_cost, tour


# ----------------------------------------------------------------------
# Test harness
# ----------------------------------------------------------------------

def _run_case(name, matrix, expected_cost=None, expected_tour=None,
              check_only_cost=False):
    cost, tour = solve_tsp(matrix)
    ok = True
    reasons = []

    if expected_cost is not None and cost != expected_cost:
        ok = False
        reasons.append(f"cost {cost} != expected {expected_cost}")

    if expected_tour is not None and not check_only_cost:
        if tour != expected_tour:
            ok = False
            reasons.append(f"tour {tour} != expected {expected_tour}")

    # Structural invariants that must always hold
    n = len(matrix)
    if tour[0] != 0 or tour[-1] != 0:
        ok = False
        reasons.append("tour must start and end at 0")
    if sorted(tour[:-1]) != list(range(n)):
        ok = False
        reasons.append("tour must visit every city exactly once")

    # Verify cost matches tour
    recomputed = sum(matrix[tour[k]][tour[k + 1]] for k in range(len(tour) - 1))
    if recomputed != cost:
        ok = False
        reasons.append(f"reported cost {cost} != recomputed {recomputed}")

    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: cost={cost}, tour={tour}")
    if not ok:
        for r in reasons:
            print(f"        -> {r}")
    return ok


def run_tests():
    all_ok = True

    # -------- Case F1: n = 1 ------------------------------------------
    m1 = [[0]]
    all_ok &= _run_case("n=1 trivial", m1, 0, [0, 0])

    # -------- Case F2: n = 2 ------------------------------------------
    m2 = [[0, 7],
          [7, 0]]
    all_ok &= _run_case("n=2 trivial", m2, 14, [0, 1, 0])

    # -------- Case A: Maximum size n = 14 -----------------------------
    # Deterministic symmetric matrix via a simple rule.
    n = 14
    m14 = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                # asymmetric-looking but symmetric because formula is symmetric
                m14[i][j] = ((i + 1) * (j + 1)) % 17 + 1
    # Ensure symmetry (formula is symmetric by construction, but be explicit)
    for i in range(n):
        for j in range(n):
            m14[i][j] = m14[j][i]
    all_ok &= _run_case("n=14 max size", m14)

    # -------- Case B: Fully degenerate (all distances equal) ----------
    n = 6
    m_eq = [[1 if i != j else 0 for j in range(n)] for i in range(n)]
    # Every tour has cost 6 (5 edges of weight 1 + return edge 1).
    # Tie-break: last-before-0 should be the smallest possible nonzero,
    # i.e. city 1. So tour should be 0 -> 2 -> 3 -> 4 -> 5 -> 1 -> 0
    # (any permutation with last = 1 and visiting all cities is optimal;
    #  our DP should pick a specific deterministic one).
    cost_eq, tour_eq = solve_tsp(m_eq)
    assert cost_eq == 6, cost_eq
    assert tour_eq[-2] == 1, f"expected last-before-0 == 1, got {tour_eq}"
    all_ok &= _run_case("degenerate equal distances", m_eq, 6, tour_eq)

    # -------- Case C: Ties at the final edge --------------------------
    # Symmetric matrix where several last cities give the same total.
    # Cities 1 and 2 are symmetric w.r.t. 0 so both give equal totals.
    m_c = [
        [0, 5, 5, 9],
        [5, 0, 2, 9],
        [5, 2, 0, 9],
        [9, 9, 9, 0],
    ]
    # Tour 0->1->2->3->0 cost = 5+2+9+9 = 25
    # Tour 0->2->1->3->0 cost = 5+2+9+9 = 25  (same)
    # Prefer smaller last city before 0; but here last is 3 in both.
    # Add a case where last differs:
    m_c2 = [
        [0, 4, 4, 4],
        [4, 0, 1, 4],
        [4, 1, 0, 4],
        [4, 4, 4, 0],
    ]
    # 0->1->2->3->0 = 4+1+4+4 = 13, last=3
    # 0->2->1->3->0 = 4+1+4+4 = 13, last=3
    # 0->3->1->2->0 = 4+4+1+4 = 13, last=2
    # 0->3->2->1->0 = 4+4+1+4 = 13, last=1  <-- smallest last
    # So optimal tour must end with ... -> 1 -> 0.
    cost_c2, tour_c2 = solve_tsp(m_c2)
    assert cost_c2 == 13, cost_c2
    assert tour_c2[-2] == 1, f"expected last-before-0 == 1, got {tour_c2}"
    all_ok &= _run_case("tie at final edge", m_c2, 13, tour_c2)

    # -------- Case D: Ties during DP transitions ----------------------
    # Many equal-cost partial paths force deterministic parent selection.
    n = 5
    m_d = [[1 if i != j else 0 for j in range(n)] for i in range(n)]
    all_ok &= _run_case("many transition ties", m_d)

    # -------- Case E: Triangle inequality violated --------------------
    # Symmetric, complete, but dist[0][2] > dist[0][1] + dist[1][2].
    m_e = [
        [0, 1, 100, 100],
        [1, 0, 1,   100],
        [100, 1, 0, 1],
        [100, 100, 1, 0],
    ]
    # Best tour: 0->1->2->3->0 = 1+1+1+100 = 103
    # Alt: 0->3->2->1->0 = 100+1+1+1 = 103, last=1
    # Alt: 0->1->3->2->0 = 1+100+1+100 = 202
    # Alt: 0->2->3->1->0 = 100+1+100+1 = 202
    # Both 103 tours end with last=3 or last=1; smaller is 1.
    cost_e, tour_e = solve_tsp(m_e)
    assert cost_e == 103, cost_e
    assert tour_e[-2] == 1, f"expected last-before-0 == 1, got {tour_e}"
    all_ok &= _run_case("triangle inequality violated", m_e, 103, tour_e)

    # -------- Classic 4-city example ----------------------------------
    m_classic = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]
    all_ok &= _run_case("classic 4-city", m_classic, 80, [0, 1, 3, 2, 0])

    print()
    print("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED")
    return all_ok


# ----------------------------------------------------------------------
# I/O entry point (unchanged output format)
# ----------------------------------------------------------------------

def main():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    idx = 0
    n = int(data[idx]); idx += 1
    distance_matrix = []
    for _ in range(n):
        row = [int(data[idx + k]) for k in range(n)]
        idx += n
        distance_matrix.append(row)

    for i in range(n):
        for j in range(n):
            if distance_matrix[i][j] != distance_matrix[j][i]:
                print("Error: Distance matrix is not symmetric")
                return

    min_cost, tour = solve_tsp(distance_matrix)
    print(f"Minimum cost: {min_cost}")
    print(f"Optimal tour: {' -> '.join(map(str, tour))}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(0 if run_tests() else 1)
    main()