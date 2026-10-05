from typing import List, Tuple, Union, Dict, Any


def traveling_salesperson(
    dist: List[List[int]],
    include_operation_summary: bool = False,
) -> Union[
    Tuple[int, List[int]],
    Dict[str, Any],
]:
    """
    Solve the symmetric Traveling Salesperson Problem using
    Held-Karp subset dynamic programming.

    Original output:
        (minimum_cost, tour)

    Optional output when include_operation_summary=True:
        {
            "cost": minimum_cost,
            "tour": tour,
            "operation_summary": {
                "major_operations": number_of_candidate_evaluations
            }
        }

    The tour starts and ends at city 0.

    Tie-breaking:
        For equal-cost DP transitions, the smaller predecessor
        city is preferred.

        For equal-cost complete tours, the smaller final city
        is preferred.

    major_operations:
        Number of predecessor/candidate transition evaluations
        performed by the Held-Karp dynamic program.
    """

    n = len(dist)

    # -------------------------
    # Input validation
    # -------------------------
    if n == 0:
        raise ValueError("Distance matrix must contain at least one city.")

    if n > 14:
        raise ValueError("The number of cities must be at most 14.")

    if any(len(row) != n for row in dist):
        raise ValueError("Distance matrix must be square.")

    for i in range(n):
        for j in range(n):
            if dist[i][j] != dist[j][i]:
                raise ValueError("Distance matrix must be symmetric.")

    if n == 1:
        cost = 0
        tour = [0, 0]

        if not include_operation_summary:
            return cost, tour

        return {
            "cost": cost,
            "tour": tour,
            "operation_summary": {
                "major_operations": 0
            },
        }

    # -------------------------
    # Held-Karp DP
    # -------------------------
    #
    # mask represents the visited cities among 1..n-1.
    #
    # dp[mask][j] =
    #   minimum cost of a path starting at 0,
    #   visiting exactly mask, and ending at j.
    #
    # predecessor[mask][j] =
    #   predecessor city of j on that optimal path.
    #
    num_masks = 1 << (n - 1)
    INF = float("inf")

    dp = [[INF] * n for _ in range(num_masks)]
    predecessor = [[-1] * n for _ in range(num_masks)]

    # Deterministic operation counter.
    major_operations = 0

    # -------------------------
    # Base cases
    # -------------------------
    for city in range(1, n):
        mask = 1 << (city - 1)

        dp[mask][city] = dist[0][city]
        predecessor[mask][city] = 0

    # -------------------------
    # DP transitions
    # -------------------------
    for mask in range(1, num_masks):
        for current in range(1, n):

            current_bit = 1 << (current - 1)

            # Current city must be included in the mask.
            if not (mask & current_bit):
                continue

            previous_mask = mask ^ current_bit

            # Singleton path: predecessor is city 0.
            if previous_mask == 0:
                continue

            best_cost = INF
            best_predecessor = -1

            # Try every possible predecessor.
            for prev in range(1, n):

                prev_bit = 1 << (prev - 1)

                if not (previous_mask & prev_bit):
                    continue

                # One major computational decision:
                # evaluate this predecessor transition.
                major_operations += 1

                candidate = (
                    dp[previous_mask][prev]
                    + dist[prev][current]
                )

                # Deterministic tie-breaking.
                if (
                    candidate < best_cost
                    or (
                        candidate == best_cost
                        and (
                            best_predecessor == -1
                            or prev < best_predecessor
                        )
                    )
                ):
                    best_cost = candidate
                    best_predecessor = prev

            dp[mask][current] = best_cost
            predecessor[mask][current] = best_predecessor

    # -------------------------
    # Close the Hamiltonian cycle
    # -------------------------
    full_mask = num_masks - 1

    best_cost = INF
    last_city = -1

    for city in range(1, n):
        candidate = dp[full_mask][city] + dist[city][0]

        if (
            candidate < best_cost
            or (
                candidate == best_cost
                and (
                    last_city == -1
                    or city < last_city
                )
            )
        ):
            best_cost = candidate
            last_city = city

    # -------------------------
    # Reconstruct optimal tour
    # -------------------------
    reversed_path = []

    mask = full_mask
    current = last_city

    while current != 0:
        reversed_path.append(current)

        prev = predecessor[mask][current]

        mask ^= 1 << (current - 1)
        current = prev

    path = [0] + list(reversed(reversed_path))
    tour = path + [0]

    cost = int(best_cost)

    # -------------------------
    # Preserve original output
    # -------------------------
    if not include_operation_summary:
        return cost, tour

    # -------------------------
    # New optional output
    # -------------------------
    return {
        "cost": cost,
        "tour": tour,
        "operation_summary": {
            "major_operations": major_operations
        },
    }


# =========================================================
# Example
# =========================================================

if __name__ == "__main__":
    distances = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]

    # Original behavior is preserved.
    cost, tour = traveling_salesperson(distances)

    print("Original output:")
    print("Cost:", cost)
    print("Tour:", tour)

    # New feature explicitly requested.
    result = traveling_salesperson(
        distances,
        include_operation_summary=True,
    )

    print("\nOutput with operation summary:")
    print(result)