from typing import Dict, List, Tuple, Union, Any


def knapsack_01(
    weights: List[int],
    values: List[int],
    capacity: int,
    include_summary: bool = False
) -> Union[List[int], Dict[str, Any]]:
    """
    Solves the 0/1 Knapsack problem handling boundary cases and 
    lexicographical tie-breaking for equal maximum values.
    """
    n = len(weights)
    
    # Handle zero capacity edge case gracefully
    if capacity < 0:
        raise ValueError("Capacity must be non-negative.")
    
    # dp[w] stores a tuple: (max_value, list_of_selected_indices)
    dp: List[Tuple[int, List[int]]] = [(0, []) for _ in range(capacity + 1)]
    
    total_evaluations = 0
    state_updates = 0
    
    for i in range(n):
        w_i = weights[i]
        v_i = values[i]
        
        # Descending capacity loop
        for w in range(capacity, w_i - 1, -1):
            total_evaluations += 1
            
            prev_val, prev_indices = dp[w - w_i]
            candidate_val = prev_val + v_i
            candidate_indices = prev_indices + [i]
            
            current_val, current_indices = dp[w]
            
            # Decision logic: strict value improvement OR lexicographical tie-break
            should_update = False
            if candidate_val > current_val:
                should_update = True
            elif candidate_val == current_val:
                if not current_indices or candidate_indices < current_indices:
                    should_update = True
                    
            if should_update:
                dp[w] = (candidate_val, candidate_indices)
                state_updates += 1
                
    # Find the overall maximum value across all valid capacities <= capacity
    max_value = max(val for val, _ in dp)
    
    # Select the lexicographically smallest index list among states achieving max_value
    best_indices: Union[List[int], None] = None
    for val, indices in dp:
        if val == max_value:
            if best_indices is None or indices < best_indices:
                best_indices = indices
                
    result_indices = best_indices if best_indices is not None else []
    
    if not include_summary:
        return result_indices
        
    return {
        "selected_indices": result_indices,
        "operation_summary": {
            "total_state_evaluations": total_evaluations,
            "state_updates": state_updates,
            "max_value_found": max_value
        }
    }


# =====================================================================
# Unit Tests for Boundary Values & Edge Cases
# =====================================================================

def run_tests():
    print("Running boundary and edge case tests...\n")
    
    # Test 1: Zero Capacity (W = 0) with non-zero weights
    res = knapsack_01(weights=[2, 3, 5], values=[10, 20, 30], capacity=0)
    assert res == [], f"Test 1 Failed: Expected [], got {res}"
    print("✓ Test 1 Passed: Zero capacity with positive weights -> []")

    # Test 2: Zero Capacity (W = 0) with zero-weight item
    res = knapsack_01(weights=[0, 2], values=[10, 20], capacity=0)
    assert res == [0], f"Test 2 Failed: Expected [0], got {res}"
    print("✓ Test 2 Passed: Zero capacity with zero-weight item -> [0]")

    # Test 3: Empty Inputs (N = 0)
    res = knapsack_01(weights=[], values=[], capacity=10)
    assert res == [], f"Test 3 Failed: Expected [], got {res}"
    print("✓ Test 3 Passed: Empty input lists -> []")

    # Test 4: All Items Exceed Capacity
    res = knapsack_01(weights=[10, 15, 20], values=[100, 200, 300], capacity=5)
    assert res == [], f"Test 4 Failed: Expected [], got {res}"
    print("✓ Test 4 Passed: All item weights exceed capacity -> []")

    # Test 5: Exact Capacity Match
    res = knapsack_01(weights=[3, 5, 2], values=[10, 20, 15], capacity=5)
    # Weights [3, 2] give total weight 5 and value 25 (indices 0 and 2)
    assert res == [0, 2], f"Test 5 Failed: Expected [0, 2], got {res}"
    print("✓ Test 5 Passed: Exact capacity combination -> [0, 2]")

    # Test 6: Lexicographical Tie-Breaking
    # Items 0 and 1 have weight 3, value 10. Item 2 has weight 3, value 10.
    # Picking item 0 vs item 1 vs item 2: lexicographically [0] < [1] < [2].
    res = knapsack_01(weights=[3, 3, 3], values=[10, 10, 10], capacity=3)
    assert res == [0], f"Test 6 Failed: Expected [0], got {res}"
    print("✓ Test 6 Passed: Lexicographical tie-breaking -> [0]")

    # Test 7: Backward Compatibility & Optional Summary Field
    summary_res = knapsack_01(weights=[2, 3], values=[3, 4], capacity=5, include_summary=True)
    assert isinstance(summary_res, dict)
    assert "selected_indices" in summary_res
    assert "operation_summary" in summary_res
    assert summary_res["selected_indices"] == [0, 1]
    print("✓ Test 7 Passed: `include_summary=True` output contract validated")

    print("\nAll boundary tests passed successfully!")


if __name__ == "__main__":
    run_tests()