from typing import List, Dict, Any
from math import comb


def traveling_salesperson(
    dist: List[List[float]],
    include_operation_summary: bool = False
) -> Dict[str, Any]:
    """
    Traveling Salesperson Solver using Held-Karp subset DP.

    Problem:
        Given a complete symmetric distance matrix with n <= 14 cities,
        find the minimum-cost Hamiltonian cycle starting and ending at
        city 0.

    Tie-breaking:
        For equal-cost DP transitions, prefer the smaller predecessor city.

    Original output:
        {
            "cost": minimum Hamiltonian cycle cost,
            "cycle": [0, ..., 0]
        }

    Optional output:
        If include_operation_summary=True:
        {
            "cost": ...,
            "cycle": [...],
            "operation_summary": {
                "major_operations": <number of DP transitions>
            }
        }

    major_operations counts every valid predecessor transition examined
    by the Held-Karp recurrence.
    """

    n = len(dist)

    # ---------------------------------------------------------
    # Validate input
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Single-city case
    # ---------------------------------------------------------
    if n == 1:
        result = {
            "cost": 0,
            "cycle": [0, 0]
        }

        if include_operation_summary:
            result["operation_summary"] = {
                "major_operations": 0
            }

        return result

    # ---------------------------------------------------------
    # Held-Karp setup
    # ---------------------------------------------------------
    # Cities 1..n-1 are represented by bits 0..n-2.
    city_count = n - 1
    state_count = 1 << city_count
    full_mask = state_count - 1

    INF = float("inf")

    # dp[mask][current] =
    # minimum cost to start at 0, visit exactly mask,
    # and finish at current.
    dp = [[INF] * n for _ in range(state_count)]

    # parent[mask][current] = selected predecessor.
    parent = [[-1] * n for _ in range(state_count)]

    major_operations = 0

    # ---------------------------------------------------------
    # Base cases: 0 -> city
    # ---------------------------------------------------------
    for city in range(1, n):
        mask = 1 << (city - 1)

        dp[mask][city] = dist[0][city]
        parent[mask][city] = 0

    # ---------------------------------------------------------
    # Held-Karp subset DP
    # ---------------------------------------------------------
    for mask in range(1, state_count):

        for current in range(1, n):

            current_bit = 1 << (current - 1)

            if not (mask & current_bit):
                continue

            previous_mask = mask ^ current_bit

            # Base case already initialized.
            if previous_mask == 0:
                continue

            best_cost = INF
            best_predecessor = -1

            # Examine every possible predecessor.
            for predecessor in range(1, n):

                predecessor_bit = 1 << (predecessor - 1)

                if not (previous_mask & predecessor_bit):
                    continue

                # One major Held-Karp transition.
                major_operations += 1

                candidate_cost = (
                    dp[previous_mask][predecessor]
                    + dist[predecessor][current]
                )

                # Minimum cost first.
                if candidate_cost < best_cost:
                    best_cost = candidate_cost
                    best_predecessor = predecessor

                # Deterministic tie-breaking:
                # smaller predecessor wins.
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

    # ---------------------------------------------------------
    # Close the cycle: last city -> 0
    # ---------------------------------------------------------
    best_cost = INF
    best_last_city = -1

    for last_city in range(1, n):

        candidate_cost = (
            dp[full_mask][last_city]
            + dist[last_city][0]
        )

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

    # ---------------------------------------------------------
    # Reconstruct cycle
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Preserve original output
    # ---------------------------------------------------------
    result = {
        "cost": best_cost,
        "cycle": cycle
    }

    # Optional feature remains opt-in.
    if include_operation_summary:
        result["operation_summary"] = {
            "major_operations": major_operations
        }

    return result


# =============================================================
# Tests
# =============================================================

if __name__ == "__main__":

    # ---------------------------------------------------------
    # Test 1: Original non-tie example
    # ---------------------------------------------------------
    distance_matrix = [
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ]

    result = traveling_salesperson(distance_matrix)

    assert result == {
        "cost": 80,
        "cycle": [0, 1, 3, 2, 0]
    }

    # ---------------------------------------------------------
    # Test 2: Optional operation_summary
    # ---------------------------------------------------------
    result_with_summary = traveling_salesperson(
        distance_matrix,
        include_operation_summary=True
    )

    assert result_with_summary["cost"] == 80
    assert result_with_summary["cycle"] == [0, 1, 3, 2, 0]
    assert "operation_summary" in result_with_summary
    assert (
        result_with_summary["operation_summary"]["major_operations"] > 0
    )

    # ---------------------------------------------------------
    # Test 3: Small deterministic tie case
    # ---------------------------------------------------------
    tie_matrix = [
        [0, 1, 1, 1],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [1, 1, 1, 0],
    ]

    tie_result = traveling_salesperson(
        tie_matrix,
        include_operation_summary=True
    )

    assert tie_result["cost"] == 4

    # Smaller predecessors are consistently selected.
    assert tie_result["cycle"] == [0, 1, 3, 2, 0]

    # Determinism check.
    assert traveling_salesperson(
        tie_matrix,
        include_operation_summary=True
    ) == tie_result

    # ---------------------------------------------------------
    # Test 4: Single-city boundary case
    # ---------------------------------------------------------
    single_city = [[0]]

    assert traveling_salesperson(single_city) == {
        "cost": 0,
        "cycle": [0, 0]
    }

    assert traveling_salesperson(
        single_city,
        include_operation_summary=True
    ) == {
        "cost": 0,
        "cycle": [0, 0],
        "operation_summary": {
            "major_operations": 0
        }
    }

    # ---------------------------------------------------------
    # Test 5: Worst-case-like maximum-size instance
    # ---------------------------------------------------------
    #
    # n = 14 is the maximum allowed size.
    #
    # Every non-diagonal edge has the same cost. Therefore:
    #   - Every Hamiltonian cycle has the same total cost.
    #   - The DP cannot rely on favorable edge weights to avoid
    #     examining predecessor transitions.
    #   - A large number of equal-cost transitions exercises the
    #     deterministic tie-breaking rule.
    #
    # This is a dense, worst-case-like Held-Karp instance.
    # ---------------------------------------------------------
    n = 14

    worst_case_matrix = [
        [0 if i == j else 1 for j in range(n)]
        for i in range(n)
    ]

    worst_result = traveling_salesperson(
        worst_case_matrix,
        include_operation_summary=True
    )

    # Every Hamiltonian cycle contains exactly 14 edges,
    # so the optimal cost is 14.
    assert worst_result["cost"] == 14

    # With equal costs and the specified predecessor rule,
    # the resulting tour is deterministic.
    assert worst_result["cycle"] == [
        0, 1, 2, 3, 4, 5, 6, 7,
        8, 9, 10, 11, 12, 13, 0
    ]

    # ---------------------------------------------------------
    # Verify the full Held-Karp transition count.
    #
    # For a subset containing k non-start cities:
    #
    #   k choices for current
    #   (k - 1) choices for predecessor
    #
    # Number of transitions:
    #
    #   C(n-1, k) * k * (k-1)
    #
    # summed over k = 2 .. n-1.
    #
    # This is Theta(n^2 * 2^n).
    # ---------------------------------------------------------
    expected_operations = sum(
        comb(n - 1, k) * k * (k - 1)
        for k in range(2, n)
    )

    assert (
        worst_result["operation_summary"]["major_operations"]
        == expected_operations
    )

    # For n=14, this confirms that the implementation actually
    # exercised the dense Held-Karp transition space rather than
    # taking a shortcut.
    assert expected_operations == 239148

    # ---------------------------------------------------------
    # Test 6: Repeat worst-case instance to verify determinism
    # ---------------------------------------------------------
    worst_result_again = traveling_salesperson(
        worst_case_matrix,
        include_operation_summary=True
    )

    assert worst_result_again == worst_result

    print("All tests passed.")
    print("Maximum-size worst-case-like instance:")
    print("Cities:", n)
    print("Optimal cost:", worst_result["cost"])
    print("Cycle:", worst_result["cycle"])
    print(
        "Major DP operations:",
        worst_result["operation_summary"]["major_operations"]
    )