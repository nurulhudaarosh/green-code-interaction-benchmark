from typing import List, Tuple


def traveling_salesperson(dist: List[List[int]]) -> Tuple[int, List[int]]:
    """
    Solve the symmetric Traveling Salesperson Problem using
    Held-Karp subset dynamic programming.

    Returns:
        (minimum_cost, tour)

    The tour starts and ends at city 0.
    For equal-cost transitions, the smaller predecessor city
    is preferred.
    """

    n = len(dist)

    # Validate input.
    if n == 0:
        raise ValueError("Distance matrix must contain at least one city.")

    if n > 14:
        raise ValueError("The number of cities must be at most 14.")

    if any(len(row) != n for row in dist):
        raise ValueError("Distance matrix must be square.")

    if n == 1:
        return 0, [0, 0]

    # dp[mask][j]:
    # Minimum cost of a path starting at city 0, visiting exactly
    # the cities in mask (among cities 1..n-1), and ending at j.
    #
    # predecessor[mask][j]:
    # Previous city on the selected optimal path.
    num_masks = 1 << (n - 1)

    INF = float("inf")

    dp = [[INF] * n for _ in range(num_masks)]
    predecessor = [[-1] * n for _ in range(num_masks)]

    # Base cases: paths directly from city 0 to each city.
    for city in range(1, n):
        mask = 1 << (city - 1)
        dp[mask][city] = dist[0][city]
        predecessor[mask][city] = 0

    # Build solutions for increasingly larger subsets.
    for mask in range(1, num_masks):
        for current in range(1, n):

            current_bit = 1 << (current - 1)

            # Current city must belong to mask.
            if not (mask & current_bit):
                continue

            previous_mask = mask ^ current_bit

            # No predecessor other than city 0 for a singleton subset.
            if previous_mask == 0:
                continue

            best_cost = INF
            best_predecessor = -1

            # Try every possible predecessor.
            for prev in range(1, n):
                prev_bit = 1 << (prev - 1)

                if not (previous_mask & prev_bit):
                    continue

                candidate = dp[previous_mask][prev] + dist[prev][current]

                # Deterministic tie-breaking:
                # smaller predecessor city wins.
                if (
                    candidate < best_cost
                    or (
                        candidate == best_cost
                        and (best_predecessor == -1 or prev < best_predecessor)
                    )
                ):
                    best_cost = candidate
                    best_predecessor = prev

            dp[mask][current] = best_cost
            predecessor[mask][current] = best_predecessor

    # All cities except city 0 have now been visited.
    full_mask = num_masks - 1

    # Close the Hamiltonian cycle by returning to city 0.
    best_cost = INF
    last_city = -1

    for city in range(1, n):
        candidate = dp[full_mask][city] + dist[city][0]

        # If complete tours have equal cost, use the smaller
        # final predecessor city for deterministic behavior.
        if (
            candidate < best_cost
            or (
                candidate == best_cost
                and (last_city == -1 or city < last_city)
            )
        ):
            best_cost = candidate
            last_city = city

    # Reconstruct the optimal path backwards.
    reversed_path = []
    mask = full_mask
    current = last_city

    while current != 0:
        reversed_path.append(current)

        prev = predecessor[mask][current]

        mask ^= 1 << (current - 1)
        current = prev

    # Reverse to obtain the forward path.
    path = [0] + reversed(reversed_path)

    # Return to city 0 to form the Hamiltonian cycle.
    tour = list(path) + [0]

    return int(best_cost), tour


# ---------------------------------------------------------
# Example
# ---------------------------------------------------------

if __name__ == "__main__":
    distances = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]

    cost, tour = traveling_salesperson(distances)

    print("Minimum cost:", cost)
    print("Tour:", tour)