from typing import List, Tuple, Dict


def minimum_hamiltonian_cycle(
    dist: List[List[int]],
) -> Tuple[int, List[int]]:
    """
    Find the minimum Hamiltonian cycle starting and ending at city 0
    using Held-Karp subset dynamic programming.

    Tie-breaking:
        If two transitions into the same DP state have equal cost,
        choose the smaller predecessor city.

    Returns:
        (minimum_cost, path)

        path starts and ends at city 0.
        For example: [0, 2, 1, 3, 0]
    """

    n = len(dist)

    # ---------- Validation ----------
    if n == 0:
        raise ValueError("Distance matrix must contain at least one city.")

    if n > 14:
        raise ValueError("The number of cities must be at most 14.")

    if any(len(row) != n for row in dist):
        raise ValueError("Distance matrix must be square.")

    if any(
        not isinstance(dist[i][j], (int, float))
        or dist[i][j] < 0
        for i in range(n)
        for j in range(n)
    ):
        raise ValueError("All distances must be non-negative numbers.")

    for i in range(n):
        if dist[i][i] != 0:
            raise ValueError("Diagonal distances must be zero.")
        for j in range(n):
            if dist[i][j] != dist[j][i]:
                raise ValueError("Distance matrix must be symmetric.")

    # ---------- Single-city case ----------
    if n == 1:
        return 0, [0, 0]

    # Only cities 1..n-1 are represented in the subset mask.
    m = n - 1
    full_mask = (1 << m) - 1

    INF = float("inf")

    # dp[(mask, j)] = minimum cost from 0 to j
    # after visiting exactly the cities in mask.
    dp: Dict[Tuple[int, int], float] = {}

    # predecessor[(mask, j)] = city immediately before j.
    predecessor: Dict[Tuple[int, int], int] = {}

    # ---------- Initialization ----------
    for city in range(1, n):
        bit = 1 << (city - 1)
        dp[(bit, city)] = dist[0][city]
        predecessor[(bit, city)] = 0

    # ---------- Held-Karp DP ----------
    for mask in range(1, full_mask + 1):

        # Cities currently contained in this mask.
        for current in range(1, n):
            current_bit = 1 << (current - 1)

            if not (mask & current_bit):
                continue

            # State containing only the current city has already
            # been initialized above.
            previous_mask = mask ^ current_bit

            if previous_mask == 0:
                continue

            best_cost = INF
            best_predecessor = None

            # Try every possible predecessor.
            for prev in range(1, n):
                prev_bit = 1 << (prev - 1)

                if not (previous_mask & prev_bit):
                    continue

                candidate = (
                    dp[(previous_mask, prev)]
                    + dist[prev][current]
                )

                if (
                    candidate < best_cost
                    or (
                        candidate == best_cost
                        and (
                            best_predecessor is None
                            or prev < best_predecessor
                        )
                    )
                ):
                    best_cost = candidate
                    best_predecessor = prev

            dp[(mask, current)] = best_cost
            predecessor[(mask, current)] = best_predecessor

    # ---------- Close the cycle ----------
    best_cost = INF
    best_last_city = None

    for last_city in range(1, n):
        candidate = dp[(full_mask, last_city)] + dist[last_city][0]

        if (
            candidate < best_cost
            or (
                candidate == best_cost
                and (
                    best_last_city is None
                    or last_city < best_last_city
                )
            )
        ):
            best_cost = candidate
            best_last_city = last_city

    # ---------- Reconstruct path ----------
    reversed_path = []
    mask = full_mask
    current = best_last_city

    while current != 0:
        reversed_path.append(current)

        prev = predecessor[(mask, current)]
        mask ^= 1 << (current - 1)
        current = prev

    path = [0] + list(reversed(reversed_path)) + [0]

    return best_cost, path


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

    minimum_cost, path = minimum_hamiltonian_cycle(distances)

    print("Minimum cost:", minimum_cost)
    print("Path:", path)