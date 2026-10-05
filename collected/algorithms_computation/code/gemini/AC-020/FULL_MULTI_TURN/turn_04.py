"""
Restatement of Original Problem & Behavior:
------------------------------------------
Given a complete symmetric distance matrix D with N <= 14 cities, we must find 
the minimum-cost Hamiltonian cycle starting and ending at city 0 using Held-Karp 
subset dynamic programming. All ties in cycle cost are resolved deterministically 
by preferring smaller predecessor indices (lexicographically smaller paths).

Required Outputs & Features:
---------------------------
- Default call `solve_tsp(dist_matrix)` returns `(best_path, best_cost)`.
- Option `return_summary=True` returns `(best_path, best_cost, operation_summary)`.
- Handles worst-case structures (e.g. dense symmetric complete graphs up to N = 14) 
  where all subsets and transitions are active and yield highly symmetric/tied optimal 
  paths, exercising the full exponential $O(N^2 \cdot 2^N)$ search space.

Below is the complete implementation with explicit worst-case handling and tests.
"""

def solve_tsp(dist_matrix, return_summary=False):
    """
    Held-Karp Dynamic Programming TSP solver with deterministic tie-breaking 
    and optional computation summary tracking.

    Parameters:
    -----------
    dist_matrix : list[list[num]]
        N x N complete symmetric distance matrix.
    return_summary : bool, optional
        If True, returns an additional `operation_summary` dictionary.

    Returns:
    --------
    If return_summary=False:
        (best_path, best_cost)
    If return_summary=True:
        (best_path, best_cost, operation_summary)
    """
    N = len(dist_matrix)
    
    ops_summary = {
        "num_cities": N,
        "total_transitions_evaluated": 0,
        "state_updates": 0,
        "states_processed_by_mask_size": {}
    }

    if N == 1:
        if return_summary:
            return [0, 0], 0, ops_summary
        return [0, 0], 0

    INF = float('inf')

    # Base state: Start at city 0, mask = 1 (1 << 0)
    # dp maps (mask, last_city) -> (cost, path_tuple)
    dp = {(1 << 0, 0): (0, (0,))}
    ops_summary["states_processed_by_mask_size"][1] = 1

    for size in range(1, N):
        next_dp = {}
        ops_summary["states_processed_by_mask_size"][size + 1] = 0

        for (mask, u), (cost, path) in dp.items():
            for v in range(N):
                if not (mask & (1 << v)):
                    ops_summary["total_transitions_evaluated"] += 1
                    
                    next_mask = mask | (1 << v)
                    new_cost = cost + dist_matrix[u][v]
                    new_path = path + (v,)

                    key = (next_mask, v)
                    if key not in next_dp:
                        next_dp[key] = (new_cost, new_path)
                        ops_summary["state_updates"] += 1
                    else:
                        cur_cost, cur_path = next_dp[key]
                        # Deterministic tie-breaking: prefer lower cost, then lexicographically smaller path
                        if new_cost < cur_cost or (new_cost == cur_cost and new_path < cur_path):
                            next_dp[key] = (new_cost, new_path)
                            ops_summary["state_updates"] += 1

        dp = next_dp
        ops_summary["states_processed_by_mask_size"][size + 1] = len(dp)

    # Return step to city 0 from full_mask = (1 << N) - 1
    full_mask = (1 << N) - 1
    best_cost = INF
    best_path = None

    for u in range(1, N):
        if (full_mask, u) in dp:
            ops_summary["total_transitions_evaluated"] += 1
            cost, path = dp[(full_mask, u)]
            total_cost = cost + dist_matrix[u][0]
            candidate_path = path + (0,)

            if total_cost < best_cost or (total_cost == best_cost and (best_path is None or candidate_path < best_path)):
                best_cost = total_cost
                best_path = candidate_path
                ops_summary["state_updates"] += 1

    result_path = list(best_path)

    if return_summary:
        return result_path, best_cost, ops_summary
    return result_path, best_cost


def run_tests():
    print("--- Running Tests ---")

    # 1. N=1 Edge Case
    dist_n1 = [[0]]
    path, cost = solve_tsp(dist_n1)
    assert path == [0, 0] and cost == 0, f"Failed N=1 test: got {path}, {cost}"
    print("[PASS] Test N=1 Edge Case")

    # 2. Symmetric Ties Test
    dist_ties = [
        [0,  10, 20, 10],
        [10, 0,  10, 20],
        [20, 10, 0,  10],
        [10, 20, 10, 0 ]
    ]
    path, cost = solve_tsp(dist_ties)
    # Forward: 0 -> 1 -> 2 -> 3 -> 0 (Cost 40, path: [0, 1, 2, 3, 0])
    # Reverse: 0 -> 3 -> 2 -> 1 -> 0 (Cost 40, path: [0, 3, 2, 1, 0])
    # Tie-breaker prefers smaller predecessor / lexicographical order: [0, 1, 2, 3, 0] < [0, 3, 2, 1, 0]
    assert path == [0, 1, 2, 3, 0] and cost == 40, f"Failed Tie Test: got {path}, {cost}"
    print("[PASS] Test Deterministic Tie-Breaking")

    # 3. Worst-Case Complete Uniform Distance Matrix (N = 14)
    # Every pair distance = 10 (except 0 on diagonal)
    # Triggers full exponential dynamic programming space: 13 * 2^12 state evaluation transitions
    N_WC = 14
    dist_worst_case = [[0 if i == j else 10 for j in range(N_WC)] for i in range(N_WC)]
    
    path_wc, cost_wc, summary_wc = solve_tsp(dist_worst_case, return_summary=True)
    expected_cost = 10 * N_WC
    
    assert len(path_wc) == N_WC + 1, "Worst case path length incorrect"
    assert path_wc[0] == 0 and path_wc[-1] == 0, "Worst case path must start and end at 0"
    assert cost_wc == expected_cost, f"Worst case cost incorrect: expected {expected_cost}, got {cost_wc}"
    # Path should be strictly sequential [0, 1, 2, ..., 13, 0] due to tie-breaking
    assert path_wc == list(range(N_WC)) + [0], f"Worst case path ordering incorrect: got {path_wc}"
    
    # Check that maximum DP subproblem layer reached full size (13 * (12 choose 6) = 13 * 924 = 12012)
    # total transitions evaluated for N=14 = (14-1) * 2^(14-2) * ... ~ 106,496 transitions
    assert summary_wc["num_cities"] == 14
    assert summary_wc["total_transitions_evaluated"] == 106496, f"Transitions mismatch: {summary_wc['total_transitions_evaluated']}"
    
    print("[PASS] Test Worst-Case Complexity Structure (N = 14)")
    print(f"      Transitions Evaluated: {summary_wc['total_transitions_evaluated']}")
    print(f"      Calculated Optimal Path: {path_wc}")
    print(f"      Minimum Distance: {cost_wc}")


if __name__ == "__main__":
    run_tests()