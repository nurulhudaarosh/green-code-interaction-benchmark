from typing import List, Dict, Any


def traveling_salesperson(dist: List[List[int]]) -> Dict[str, Any]:
    """
    Solve the symmetric Traveling Salesperson Problem using
    Held-Karp subset dynamic programming.

    Input:
        dist: n x n complete symmetric distance matrix.

    Output:
        {
            "min_cost": minimum Hamiltonian cycle cost,
            "tour": optimal tour starting and ending at city 0
        }

    Tie-breaking:
        When two predecessors give the same minimum cost,
        choose the smaller predecessor.
    """

    n = len(dist)

    # ---------- Validate input ----------
    if not 1 <= n <= 14:
        raise ValueError("Number of cities must be between 1 and 14.")

    if any(len(row) != n for row in dist):
        raise ValueError("Distance matrix must be square.")

    for i in range(n):
        for j in range(n):
            if dist[i][j] < 0:
                raise ValueError("Distances must be non-negative.")
            if dist[i][j] != dist[j][i]:
                raise ValueError("Distance matrix must be symmetric.")

    # ---------- Single-city case ----------
    if n == 1:
        return {
            "min_cost": 0,
            "tour": [0, 0]
        }

    # We exclude city 0 from the subsets.
    #
    # Bit k represents city k+1.
    # Example for n=4:
    # bit 0 -> city 1
    # bit 1 -> city 2
    # bit 2 -> city 3

    m = n - 1
    total_masks = 1 << m
    INF = float("inf")

    # dp[mask][j]:
    # minimum cost to start at city 0,
    # visit exactly the cities in mask,
    # and finish at city j.
    #
    # j is represented by its actual city number (1..n-1).
    dp = [[INF] * n for _ in range(total_masks)]

    # parent[mask][j]:
    # predecessor city used to reach j optimally.
    parent = [[-1] * n for _ in range(total_masks)]

    # ---------- Base cases ----------
    for city in range(1, n):
        mask = 1 << (city - 1)
        dp[mask][city] = dist[0][city]
        parent[mask][city] = 0

    # ---------- Held-Karp DP ----------
    #
    # For each subset, try every possible final city.
    # If predecessor costs tie, choose the smaller predecessor.
    for mask in range(1, total_masks):
        for city in range(1, n):

            city_bit = 1 << (city - 1)

            # City must belong to the current subset.
            if not (mask & city_bit):
                continue

            previous_mask = mask ^ city_bit

            # No predecessor for singleton subsets.
            if previous_mask == 0:
                continue

            best_cost = INF
            best_prev = -1

            # Try every possible predecessor.
            for prev in range(1, n):
                prev_bit = 1 << (prev - 1)

                if not (previous_mask & prev_bit):
                    continue

                candidate = dp[previous_mask][prev] + dist[prev][city]

                # Deterministic tie-breaking:
                # smaller predecessor wins.
                if (
                    candidate < best_cost
                    or (
                        candidate == best_cost
                        and (best_prev == -1 or prev < best_prev)
                    )
                ):
                    best_cost = candidate
                    best_prev = prev

            dp[mask][city] = best_cost
            parent[mask][city] = best_prev

    # ---------- Close the Hamiltonian cycle ----------
    full_mask = total_masks - 1

    min_cost = INF
    last_city = -1

    for city in range(1, n):
        candidate = dp[full_mask][city] + dist[city][0]

        # If final costs tie, choose the smaller final city.
        if (
            candidate < min_cost
            or (
                candidate == min_cost
                and (last_city == -1 or city < last_city)
            )
        ):
            min_cost = candidate
            last_city = city

    # ---------- Reconstruct tour ----------
    reversed_tour = []
    mask = full_mask
    city = last_city

    while city != 0:
        reversed_tour.append(city)

        previous_city = parent[mask][city]

        mask ^= 1 << (city - 1)
        city = previous_city

    # Reconstruct from city 0 to the final city.
    tour = [0] + list(reversed(reversed_tour)) + [0]

    return {
        "min_cost": min_cost,
        "tour": tour
    }


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

    result = traveling_salesperson(distances)

    print(result)