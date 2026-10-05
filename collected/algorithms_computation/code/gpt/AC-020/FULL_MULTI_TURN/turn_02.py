from typing import List, Dict, Any


def traveling_salesperson(dist: List[List[float]]) -> Dict[str, Any]:
    """
    Traveling Salesperson Solver using Held-Karp subset DP.

    Problem:
        Given a complete symmetric distance matrix with n <= 14 cities,
        find the minimum-cost Hamiltonian cycle starting and ending at
        city 0.

    Tie-breaking:
        Whenever equal-cost DP transitions occur, prefer the smaller
        predecessor city.

    Returns exactly:
        {
            "cost": minimum Hamiltonian cycle cost,
            "cycle": [0, ..., 0]
        }
    """

    n = len(dist)

    # -------------------------
    # Input validation
    # -------------------------
    if not 1 <= n <= 14:
        raise ValueError("Number of cities must be between 1 and 14.")

    if any(len(row) != n for row in dist):
        raise ValueError("Distance matrix must be square.")

    for i in range(n):
        if dist[i][i] != 0:
            raise ValueError("Diagonal distances must be 0.")

        for j in range(n):
            if dist[i][j] < 0:
                raise ValueError("Distances must be non-negative.")

            if dist[i][j] != dist[j][i]:
                raise ValueError("Distance matrix must be symmetric.")

    # -------------------------
    # Single-city case
    # -------------------------
    if n == 1:
        return {
            "cost": 0,
            "cycle": [0, 0]
        }

    # Cities 1..n-1 are represented by bits 0..n-2.
    city_count = n - 1
    state_count = 1 << city_count
    full_mask = state_count - 1

    INF = float("inf")

    # dp[mask][city]:
    # Minimum cost to start at 0, visit exactly the cities in mask,
    # and finish at 'city'.
    dp = [[INF] * n for _ in range(state_count)]

    # parent[mask][city]:
    # The predecessor city used to obtain this state.
    parent = [[-1] * n for _ in range(state_count)]

    # -------------------------
    # Base cases
    # -------------------------
    for city in range(1, n):
        mask = 1 << (city - 1)

        dp[mask][city] = dist[0][city]
        parent[mask][city] = 0

    # -------------------------
    # Held-Karp DP
    # -------------------------
    for mask in range(1, state_count):
        for current in range(1, n):

            current_bit = 1 << (current - 1)

            # Current city must belong to this subset.
            if not (mask & current_bit):
                continue

            previous_mask = mask ^ current_bit

            # Already initialized as 0 -> current.
            if previous_mask == 0:
                continue

            best_cost = INF
            best_predecessor = -1

            # Try every possible predecessor.
            for predecessor in range(1, n):
                predecessor_bit = 1 << (predecessor - 1)

                if not (previous_mask & predecessor_bit):
                    continue

                previous_cost = dp[previous_mask][predecessor]

                if previous_cost == INF:
                    continue

                candidate_cost = (
                    previous_cost + dist[predecessor][current]
                )

                # Deterministic tie rule:
                # equal cost -> smaller predecessor.
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_predecessor = predecessor

                elif (
                    candidate_cost == best_cost
                    and (
                        best_predecessor == -1
                        or predecessor < best_predecessor
                    )
                ):
                    best_predecessor = predecessor

            dp[mask][current] = best_cost
            parent[mask][current] = best_predecessor

    # -------------------------
    # Close the Hamiltonian cycle
    # -------------------------
    #
    # The final edge is current -> 0.
    # Therefore, when two complete tours have equal cost,
    # the "predecessor of 0" is the final city.
    #
    best_cost = INF
    best_last_city = -1

    for last_city in range(1, n):

        candidate_cost = dp[full_mask][last_city] + dist[last_city][0]

        if candidate_cost < best_cost:
            best_cost = candidate_cost
            best_last_city = last_city

        elif (
            candidate_cost == best_cost
            and (
                best_last_city == -1
                or last_city < best_last_city
            )
        ):
            best_last_city = last_city

    # -------------------------
    # Reconstruct the cycle
    # -------------------------
    reversed_path = []

    mask = full_mask
    current = best_last_city

    while current != 0:
        reversed_path.append(current)

        predecessor = parent[mask][current]

        if predecessor == -1:
            raise RuntimeError("Failed to reconstruct optimal tour.")

        mask ^= 1 << (current - 1)
        current = predecessor

    cycle = [0] + list(reversed(reversed_path)) + [0]

    return {
        "cost": best_cost,
        "cycle": cycle
    }


# =========================================================
# Demonstration of deterministic tie handling
# =========================================================
#
# Every move between different cities costs 1.
# Therefore every Hamiltonian cycle has total cost 4.
#
# The deterministic rule must consistently choose the
# smaller predecessor when equal-cost DP transitions occur.
# =========================================================

if __name__ == "__main__":

    tie_matrix = [
        [0, 1, 1, 1],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [1, 1, 1, 0],
    ]

    result = traveling_salesperson(tie_matrix)

    print("Tie-case result:")
    print(result)

    assert result["cost"] == 4

    # With the specified predecessor tie rule, the deterministic
    # reconstruction is:
    assert result["cycle"] == [0, 1, 3, 2, 0]

    # A second call must produce exactly the same result.
    result_again = traveling_salesperson(tie_matrix)

    assert result_again == result

    # -----------------------------------------------------
    # Non-tie example
    # -----------------------------------------------------

    distance_matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]

    result = traveling_salesperson(distance_matrix)

    print("\nNormal result:")
    print(result)

    assert result["cost"] == 80
    assert result["cycle"] == [0, 1, 3, 2, 0]

    print("\nAll tests passed.")