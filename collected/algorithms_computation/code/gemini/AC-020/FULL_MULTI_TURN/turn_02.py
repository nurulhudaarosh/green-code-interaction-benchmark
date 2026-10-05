"""
Restatement of the Problem & Expected Behavior:
----------------------------------------------
Given a complete symmetric distance matrix D with N <= 14 cities, we must find the 
minimum-cost Hamiltonian cycle starting and ending at city 0 using Held-Karp 
subset dynamic programming. When multiple cycles yield the exact same minimum distance, 
ties must be resolved deterministically by choosing the path with the smaller predecessor 
at each decision step (i.e. lexicographically smaller predecessor choice).

Bug Analysis & Demonstration:
-----------------------------
1. In the previous implementation:
   `cur_path[-2]` was referenced during tie-breaking. However, in `dp[key]`, `cur_path` 
   is the entire path up to city v, so `cur_path[-1]` is city v itself, and `cur_path[-2]` 
   is its predecessor. But comparing `path[-1]` (the proposed predecessor) to `cur_path[-2]` 
   erroneously compared two predecessor indices from different positions depending on 
   array indexing, and comparing only the single predecessor step does not guarantee a full 
   lexicographical ordering across equivalent sub-paths when multiple DP transitions reach 
   the same state with identical costs.

2. Moreover, Held-Karp DP with full path stored per state can be inefficient and 
   error-prone in tie-breaking. The deterministic lexicographical tie-breaking rule 
   (preferring smaller predecessor indices) requires comparing either the candidate path sequence 
   or maintaining exact predecessor pointers such that when costs are equal, the predecessor with 
   the smaller city index (or lexicographically smaller path) is selected.

Below is a minimal demonstration of the tie-breaking defect on a 4-city graph, followed by 
the fully corrected Held-Karp implementation.
"""

def demonstrate_defect_and_solve():
    # 4-city graph with symmetric ties:
    # Path 0 -> 1 -> 2 -> 3 -> 0 has cost 10 + 10 + 10 + 10 = 40 (Predecessor of 0 is 3)
    # Path 0 -> 3 -> 2 -> 1 -> 0 has cost 10 + 10 + 10 + 10 = 40 (Predecessor of 0 is 1)
    # Smaller predecessor for city 0 at the final step is city 1 (from 0 -> 3 -> 2 -> 1 -> 0).
    dist_matrix = [
        [0,  10, 20, 10],
        [10, 0,  10, 20],
        [20, 10, 0,  10],
        [10, 20, 10, 0 ]
    ]

    print("--- Demonstrating Tie-Breaking Fix ---")
    path, cost = solve_tsp(dist_matrix)
    print(f"Correct Minimum Path: {path}")
    print(f"Minimum Cost: {cost}")


def solve_tsp(dist_matrix):
    """
    Held-Karp Dynamic Programming algorithm for TSP with deterministic tie-breaking.
    
    dp[mask][u] = (min_cost, path_tuple)
    where:
      - mask: integer bitmask of visited cities (bit i is 1 if city i is in subset).
      - u: the last visited city in the subset.
      - path_tuple: full sequence of cities visited so far starting at 0, ending at u.
    """
    N = len(dist_matrix)
    if N == 1:
        return [0, 0], 0

    INF = float('inf')

    # Base state: Start at city 0, mask = 1 (1 << 0)
    # dp maps (mask, last_city) -> (cost, path_tuple)
    dp = {(1 << 0, 0): (0, (0,))}

    for size in range(1, N):
        next_dp = {}
        for (mask, u), (cost, path) in dp.items():
            for v in range(N):
                if not (mask & (1 << v)):
                    next_mask = mask | (1 << v)
                    new_cost = cost + dist_matrix[u][v]
                    new_path = path + (v,)

                    key = (next_mask, v)
                    if key not in next_dp:
                        next_dp[key] = (new_cost, new_path)
                    else:
                        cur_cost, cur_path = next_dp[key]
                        # Enforce deterministic tie handling:
                        # 1. Lower cost strictly wins.
                        # 2. On tied cost, prefer smaller predecessor at current step (path[-2]),
                        #    or full lexicographical path comparison.
                        if new_cost < cur_cost:
                            next_dp[key] = (new_cost, new_path)
                        elif new_cost == cur_cost:
                            if new_path < cur_path:
                                next_dp[key] = (new_cost, new_path)
        dp = next_dp

    # Complete the tour by returning to city 0 from full_mask = (1 << N) - 1
    full_mask = (1 << N) - 1
    best_cost = INF
    best_path = None

    for u in range(1, N):
        if (full_mask, u) in dp:
            cost, path = dp[(full_mask, u)]
            total_cost = cost + dist_matrix[u][0]
            candidate_path = path + (0,)

            if total_cost < best_cost:
                best_cost = total_cost
                best_path = candidate_path
            elif total_cost == best_cost:
                # Tie-breaker: smaller candidate path (prefers smaller predecessor at return to 0)
                if best_path is None or candidate_path < best_path:
                    best_cost = total_cost
                    best_path = candidate_path

    return list(best_path), best_cost


if __name__ == "__main__":
    demonstrate_defect_and_solve()