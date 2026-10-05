from typing import List, Dict, Any
import unittest


def traveling_salesperson(dist: List[List[int]]) -> Dict[str, Any]:
    """
    Traveling Salesperson Solver using Held-Karp subset DP.

    Problem:
        Given a complete symmetric distance matrix with at most
        14 cities, find the minimum Hamiltonian cycle starting
        and ending at city 0.

    Output:
        {
            "min_cost": minimum cycle cost,
            "tour": optimal tour starting and ending at 0
        }

    Tie-breaking:
        If two predecessors produce the same minimum cost,
        choose the smaller predecessor.
    """

    n = len(dist)

    # Validate number of cities.
    if not 1 <= n <= 14:
        raise ValueError("Number of cities must be between 1 and 14.")

    # Validate square matrix.
    if any(len(row) != n for row in dist):
        raise ValueError("Distance matrix must be square.")

    # Validate non-negative and symmetric distances.
    for i in range(n):
        for j in range(n):
            if dist[i][j] < 0:
                raise ValueError("Distances must be non-negative.")
            if dist[i][j] != dist[j][i]:
                raise ValueError("Distance matrix must be symmetric.")

    # Single-city case.
    if n == 1:
        return {
            "min_cost": 0,
            "tour": [0, 0]
        }

    # Cities 1..n-1 are represented by bits 0..n-2.
    m = n - 1
    total_masks = 1 << m
    INF = float("inf")

    # dp[mask][city] = minimum cost to start at 0,
    # visit exactly the cities in mask, and finish at city.
    dp = [[INF] * n for _ in range(total_masks)]

    # parent[mask][city] = predecessor city.
    parent = [[-1] * n for _ in range(total_masks)]

    # Base cases: 0 -> city.
    for city in range(1, n):
        mask = 1 << (city - 1)
        dp[mask][city] = dist[0][city]
        parent[mask][city] = 0

    # Held-Karp subset dynamic programming.
    for mask in range(1, total_masks):
        for city in range(1, n):

            city_bit = 1 << (city - 1)

            if not (mask & city_bit):
                continue

            previous_mask = mask ^ city_bit

            # Singleton subset is already initialized.
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

                # Smaller predecessor wins ties.
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

    # Close the Hamiltonian cycle by returning to city 0.
    full_mask = total_masks - 1

    min_cost = INF
    last_city = -1

    for city in range(1, n):
        candidate = dp[full_mask][city] + dist[city][0]

        # Deterministic tie-breaking for final city.
        if (
            candidate < min_cost
            or (
                candidate == min_cost
                and (last_city == -1 or city < last_city)
            )
        ):
            min_cost = candidate
            last_city = city

    # Reconstruct optimal tour.
    reversed_tour = []
    mask = full_mask
    city = last_city

    while city != 0:
        reversed_tour.append(city)

        previous_city = parent[mask][city]

        mask ^= 1 << (city - 1)
        city = previous_city

    tour = [0] + list(reversed(reversed_tour)) + [0]

    return {
        "min_cost": min_cost,
        "tour": tour
    }


# ============================================================
# TESTS
# ============================================================

class TestTravelingSalesperson(unittest.TestCase):

    # Test 1: Single city
    def test_single_city(self):
        dist = [
            [0]
        ]

        self.assertEqual(
            traveling_salesperson(dist),
            {
                "min_cost": 0,
                "tour": [0, 0]
            }
        )

    # Test 2: Two cities
    def test_two_cities(self):
        dist = [
            [0, 7],
            [7, 0]
        ]

        self.assertEqual(
            traveling_salesperson(dist),
            {
                "min_cost": 14,
                "tour": [0, 1, 0]
            }
        )

    # Test 3: Standard 4-city example
    def test_four_city_example(self):
        dist = [
            [0, 10, 15, 20],
            [10, 0, 35, 25],
            [15, 35, 0, 30],
            [20, 25, 30, 0]
        ]

        self.assertEqual(
            traveling_salesperson(dist),
            {
                "min_cost": 80,
                "tour": [0, 1, 3, 2, 0]
            }
        )

    # Test 4: Maximum-size, worst-case-like structure.
    #
    # n = 14 gives:
    #     2^(14-1) = 8192 subset masks
    #
    # All non-diagonal edges have equal cost, so many
    # optimal solutions exist and deterministic tie handling
    # is exercised heavily.
    def test_14_city_equal_weights(self):
        n = 14

        dist = [
            [
                0 if i == j else 1
                for j in range(n)
            ]
            for i in range(n)
        ]

        result = traveling_salesperson(dist)

        # Every Hamiltonian cycle contains 14 edges.
        self.assertEqual(result["min_cost"], 14)

        tour = result["tour"]

        # Starts and ends at city 0.
        self.assertEqual(tour[0], 0)
        self.assertEqual(tour[-1], 0)

        # Contains exactly 14 distinct cities.
        self.assertEqual(len(tour), 15)
        self.assertEqual(sorted(tour[:-1]), list(range(14)))
        self.assertEqual(len(set(tour[:-1])), 14)

    # Test 5: Maximum-size structured matrix.
    #
    # The cycle:
    # 0 -> 1 -> 2 -> ... -> 13 -> 0
    #
    # has cost 14 and all other edges cost 100.
    def test_14_city_structured(self):
        n = 14

        dist = [
            [0] * n
            for _ in range(n)
        ]

        # Expensive default edges.
        for i in range(n):
            for j in range(n):
                if i != j:
                    dist[i][j] = 100

        # Cheap intended cycle.
        for i in range(n - 1):
            dist[i][i + 1] = 1
            dist[i + 1][i] = 1

        dist[0][13] = 1
        dist[13][0] = 1

        result = traveling_salesperson(dist)

        self.assertEqual(result["min_cost"], 14)

        self.assertEqual(
            result["tour"],
            [
                0, 1, 2, 3, 4, 5, 6,
                7, 8, 9, 10, 11, 12,
                13, 0
            ]
        )

    # Test 6: Explicit predecessor tie-breaking.
    def test_smaller_predecessor_tie_breaking(self):
        dist = [
            [0, 1, 1, 2],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [2, 1, 1, 0]
        ]

        result = traveling_salesperson(dist)

        self.assertEqual(result["min_cost"], 4)

        self.assertEqual(
            result["tour"],
            [0, 1, 2, 3, 0]
        )

    # Test 7: Too many cities.
    def test_too_many_cities(self):
        dist = [
            [0] * 15
            for _ in range(15)
        ]

        with self.assertRaises(ValueError):
            traveling_salesperson(dist)

    # Test 8: Non-square matrix.
    def test_non_square_matrix(self):
        dist = [
            [0, 1],
            [1]
        ]

        with self.assertRaises(ValueError):
            traveling_salesperson(dist)

    # Test 9: Non-symmetric matrix.
    def test_non_symmetric_matrix(self):
        dist = [
            [0, 2],
            [3, 0]
        ]

        with self.assertRaises(ValueError):
            traveling_salesperson(dist)

    # Test 10: Negative distance.
    def test_negative_distance(self):
        dist = [
            [0, -1],
            [-1, 0]
        ]

        with self.assertRaises(ValueError):
            traveling_salesperson(dist)


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    unittest.main()