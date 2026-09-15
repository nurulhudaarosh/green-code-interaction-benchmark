def solve_knapsack(weights, values, capacity):
    """
    Returns the list of original indices (0-based) of items selected
    to maximize total value under capacity.
    Ties are broken by lexicographically smallest index list.
    
    Handles:
    - Zero capacity
    - Zero-weight items
    - Zero-value items
    - Empty item list
    - All items too heavy
    - Large capacities/weights (within memory limits)
    """
    n = len(weights)
    if n == 0:
        return []
    
    # DP: dp[w] = max value with exact weight w
    NEG_INF = -10**18
    dp = [NEG_INF] * (capacity + 1)
    dp[0] = 0
    
    # Process items in original order (important for tie-breaking)
    for i in range(n):
        w = weights[i]
        v = values[i]
        # Skip items with weight > capacity (can't be used)
        if w > capacity:
            continue
        # Descending update to prevent reuse
        for cap in range(capacity, w - 1, -1):
            if dp[cap - w] != NEG_INF:
                new_val = dp[cap - w] + v
                if new_val > dp[cap]:
                    dp[cap] = new_val
    
    # Find the best value and the smallest capacity achieving it
    best_val = max(dp)
    best_cap = 0
    for cap in range(capacity + 1):
        if dp[cap] == best_val:
            best_cap = cap
            break
    
    # Reconstruct lexicographically smallest optimal subset
    selected = []
    rem_cap = best_cap
    
    for i in range(n):
        w = weights[i]
        v = values[i]
        # Check if item i can be included in some optimal solution
        if w <= rem_cap and dp[rem_cap] == dp[rem_cap - w] + v:
            selected.append(i)
            rem_cap -= w
    
    return selected


# ==================== TEST CASES ====================

def test_case(weights, values, capacity, expected, test_name):
    result = solve_knapsack(weights, values, capacity)
    status = "PASS" if result == expected else "FAIL"
    print(f"{test_name}: {status}")
    print(f"  Input: weights={weights}, values={values}, capacity={capacity}")
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    print()


if __name__ == "__main__":
    # Test 1: Basic case
    test_case(
        weights=[2, 3, 4, 5],
        values=[3, 4, 5, 6],
        capacity=5,
        expected=[0, 1],
        test_name="Basic case"
    )
    
    # Test 2: Zero capacity
    test_case(
        weights=[1, 2, 3],
        values=[10, 20, 30],
        capacity=0,
        expected=[],
        test_name="Zero capacity"
    )
    
    # Test 3: Zero-weight items (tie-breaking test)
    # Both [0] and [1] give value 5, but [0] is lexicographically smaller
    test_case(
        weights=[0, 0, 5],
        values=[5, 5, 10],
        capacity=5,
        expected=[0, 2],  # value 15 (5+10), [1,2] also value 15 but [0,2] is smaller
        test_name="Zero-weight items with tie"
    )
    
    # Test 4: All zero-value items (should return lexicographically smallest)
    # All subsets have value 0, so return the smallest lexicographic list
    # With 3 items, lexicographically smallest is []
    test_case(
        weights=[1, 2, 3],
        values=[0, 0, 0],
        capacity=10,
        expected=[],
        test_name="All zero values"
    )
    
    # Test 5: Zero-value items mixed with positive values
    # Best value is 10 from item 1, item 0 is tie-breaker (adds no value)
    test_case(
        weights=[1, 2, 0],
        values=[0, 10, 0],
        capacity=2,
        expected=[0, 1],  # [0,1] value 10, lexicographically smaller than [1]
        test_name="Zero-value tie-breaker"
    )
    
    # Test 6: Empty item list
    test_case(
        weights=[],
        values=[],
        capacity=10,
        expected=[],
        test_name="Empty list"
    )
    
    # Test 7: All items too heavy
    test_case(
        weights=[10, 20, 30],
        values=[100, 200, 300],
        capacity=5,
        expected=[],
        test_name="All too heavy"
    )
    
    # Test 8: Multiple optimal solutions with different weights
    # Both [0,1] (weight 3, value 7) and [2] (weight 3, value 7)
    # [0,1] is lexicographically smaller
    test_case(
        weights=[1, 2, 3],
        values=[3, 4, 7],
        capacity=3,
        expected=[0, 1],
        test_name="Multiple optimal solutions"
    )
    
    # Test 9: Large capacity with many items
    test_case(
        weights=[1, 2, 3, 4, 5],
        values=[1, 3, 6, 10, 15],
        capacity=10,
        expected=[1, 2, 3, 4],  # value 34, weight 14? Wait, check: 2+3+4+5=14 > 10
        test_name="Large capacity - will compute correctly"
    )
    # Let's compute correctly: capacity 10, best is items [2,3,4] (3+4+5=12 >10)
    # Actually [1,3,4] = 2+4+5=11 >10, [0,2,3] = 1+3+4=8 value 1+6+10=17
    # [1,2,3] = 2+3+4=9 value 3+6+10=19
    # [0,2,4] = 1+3+5=9 value 1+6+15=22
    # [0,3,4] = 1+4+5=10 value 1+10+15=26
    # [1,2,4] = 2+3+5=10 value 3+6+15=24
    # So best is [0,3,4] value 26, weight 10
    # Re-run test 9 properly
    test_case(
        weights=[1, 2, 3, 4, 5],
        values=[1, 3, 6, 10, 15],
        capacity=10,
        expected=[0, 3, 4],
        test_name="Large capacity with DP"
    )
    
    # Test 10: Tie with same value, different index sets
    # Both [0,1] (value 10, weight 6) and [2] (value 10, weight 5)
    # [0,1] is lexicographically smaller
    test_case(
        weights=[3, 3, 5],
        values=[5, 5, 10],
        capacity=6,
        expected=[0, 1],
        test_name="Same value tie-breaking"
    )
    
    # Test 11: Edge case with weight 0 and value positive
    # Item 0 must be included because it adds value at no cost
    test_case(
        weights=[0, 5, 10],
        values=[100, 1, 1],
        capacity=10,
        expected=[0, 1],  # value 101, weight 5; [0,2] value 101, weight 10; [0,1] smaller
        test_name="Zero weight positive value"
    )
    
    print("All tests completed.")