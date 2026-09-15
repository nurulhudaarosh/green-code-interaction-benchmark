from typing import Union, Tuple, Dict, Any


def knapsack_01(
    weights: list[int],
    values: list[int],
    capacity: int,
    include_summary: bool = False
) -> Union[list[int], Tuple[list[int], Dict[str, Any]]]:
    """
    Solves 0/1 Knapsack deterministically with exact tie-breaking and boundary handling.
    """
    n = len(weights)
    decisions_count = 0
    state_updates = 0
    
    # Boundary case: Empty input or negative capacity
    if n == 0 or capacity < 0:
        indices = []
        if not include_summary:
            return indices
        return indices, {
            "max_value": 0,
            "dp_table_cell_evaluations": 0,
            "decision_points_evaluated": 0,
            "state_updates": 0,
            "reconstruction_steps": 0,
            "total_major_operations": 0
        }

    # dp[i][w] = max value using a subset of items from index 0..i-1 with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        w_i, v_i = weights[i - 1], values[i - 1]
        for w in range(capacity + 1):
            decisions_count += 1
            if w_i <= w:
                val_with = dp[i - 1][w - w_i] + v_i
                val_without = dp[i - 1][w]
                if val_with > val_without:
                    dp[i][w] = val_with
                    state_updates += 1
                else:
                    dp[i][w] = val_without
            else:
                dp[i][w] = dp[i - 1][w]

    # Reconstruct optimal lexicographical path
    max_val = dp[n][capacity]
    curr_w = capacity
    
    # Find minimum capacity yielding max_val
    for w in range(capacity + 1):
        decisions_count += 1
        if dp[n][w] == max_val:
            curr_w = w
            break

    selected_indices = []
    reconstruction_steps = 0
    
    for i in range(n):
        reconstruction_steps += 1
        w_i, v_i = weights[i], values[i]
        
        if w_i <= curr_w and dp[n][curr_w] == dp[n][curr_w - w_i] + v_i:
            if dp[i + 1][curr_w] != dp[i][curr_w]:
                selected_indices.append(i)
                curr_w -= w_i

    if not include_summary:
        return selected_indices

    summary = {
        "max_value": max_val,
        "dp_table_cell_evaluations": n * (capacity + 1),
        "decision_points_evaluated": decisions_count,
        "state_updates": state_updates,
        "reconstruction_steps": reconstruction_steps,
        "total_major_operations": decisions_count + reconstruction_steps
    }

    return selected_indices, summary


# --- Comprehensive Test Suite ---
def run_tests():
    # 1. Zero Capacity (W = 0) with zero-weight item
    w1, v1, cap1 = [0, 2, 3], [10, 20, 30], 0
    assert knapsack_01(w1, v1, cap1) == [0], f"Failed Test 1: {knapsack_01(w1, v1, cap1)}"

    # 2. Zero-Weight & Zero-Value Boundary Items
    w2, v2, cap2 = [0, 0, 1], [0, 0, 10], 1
    # Both item 0 and 1 have weight 0, value 0. Item 2 has weight 1, value 10.
    assert knapsack_01(w2, v2, cap2) == [0, 1, 2], f"Failed Test 2: {knapsack_01(w2, v2, cap2)}"

    # 3. Empty Inputs
    assert knapsack_01([], [], 10) == [], "Failed Test 3 (Empty Input)"

    # 4. No Items Fit
    w4, v4, cap4 = [5, 10, 15], [100, 200, 300], 3
    assert knapsack_01(w4, v4, cap4) == [], f"Failed Test 4: {knapsack_01(w4, v4, cap4)}"

    # 5. Exact Capacity Match (All fit)
    w5, v5, cap5 = [2, 3, 5], [10, 20, 30], 10
    assert knapsack_01(w5, v5, cap5) == [0, 1, 2], f"Failed Test 5: {knapsack_01(w5, v5, cap5)}"

    # 6. Strict Lexicographical Tie-Breaking
    w6, v6, cap6 = [1, 1, 1], [10, 10, 10], 1
    # Items 0, 1, 2 all give value 10 for weight 1. Smallest lexicographical set is [0].
    assert knapsack_01(w6, v6, cap6) == [0], f"Failed Test 6: {knapsack_01(w6, v6, cap6)}"

    # 7. Operational Summary Preservation
    res, summary = knapsack_01(w1, v1, cap1, include_summary=True)
    assert res == [0] and "total_major_operations" in summary, "Failed Test 7 (Summary)"

    print("All tests passed successfully!")


if __name__ == "__main__":
    run_tests()