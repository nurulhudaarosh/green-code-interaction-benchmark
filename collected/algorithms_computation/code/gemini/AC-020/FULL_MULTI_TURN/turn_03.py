"""
Restatement of Original Problem & Behavior:
------------------------------------------
Given a complete symmetric distance matrix D with at most N <= 14 cities, we must 
find the minimum-cost Hamiltonian cycle starting and ending at city 0 using Held-Karp 
subset dynamic programming. All ties in cycle cost are resolved deterministically by 
preferring smaller predecessor indices (lexicographically smaller paths).

Original Required Outputs:
--------------------------
1. Optimal cycle path (list of city indices starting and ending at 0).
2. Minimum total distance/cost of the path.

New Feature Addition:
---------------------
An optional parameter `return_summary` (default=False) is added to `solve_tsp`.
- When `return_summary=False` (default/disabled), the function returns `(best_path, best_cost)`, 
  maintaining 100% backward compatibility with all original requirements.
- When `return_summary=True`, the function returns `(best_path, best_cost, operation_summary)`, 
  where `operation_summary` is a dictionary containing deterministic metrics of the computation 
  (e.g., total subproblem transitions evaluated, total state updates, states processed per layer).
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
    
    # Operation Summary Counters
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
                        # Deterministic tie handling: lower cost or lexicographically smaller path
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


if __name__ == "__main__":
    # Standard 4-city test matrix
    dist = [
        [0,  10, 20, 10],
        [10, 0,  10, 20],
        [20, 10, 0,  10],
        [10, 20, 10, 0 ]
    ]

    # 1. Verification with default behavior (return_summary=False)
    path, cost = solve_tsp(dist)
    print("--- Backward-Compatible Call (return_summary=False) ---")
    print(f"Path: {path}")
    print(f"Cost: {cost}")

    # 2. Verification with summary output (return_summary=True)
    path, cost, summary = solve_tsp(dist, return_summary=True)
    print("\n--- Extended Call (return_summary=True) ---")
    print(f"Path: {path}")
    print(f"Cost: {cost}")
    print(f"Operation Summary: {summary}")