def get_lexicographically_smallest_lis_indices(arr: list[int]) -> list[int]:
    """
    Finds a strictly increasing subsequence of maximum length from `arr`
    and returns the lexicographically smallest sequence of original indices.

    Handles empty inputs, single element arrays, duplicate/equal structures,
    and strictly decreasing structures seamlessly.
    
    Time Complexity: O(N^2)
    Space Complexity: O(N^2)
    """
    n = len(arr)
    # Edge case: Empty structure
    if n == 0:
        return []

    dp = [1] * n
    # Stores the optimal predecessor path for each index
    paths = [[i] for i in range(n)]

    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                candidate_path = paths[j] + [i]
                candidate_len = len(candidate_path)

                if candidate_len > dp[i]:
                    dp[i] = candidate_len
                    paths[i] = candidate_path
                elif candidate_len == dp[i]:
                    # Tie-breaking rule: pick lexicographically smaller index path
                    if candidate_path < paths[i]:
                        paths[i] = candidate_path

    # Find the maximum route length
    max_len = max(dp)

    # Gather all paths achieving max_len and pick the lexicographically smallest
    best_path = min(path for path in paths if len(path) == max_len)

    return best_path


# ==========================================
# Test Suite Covering Hard & Boundary Cases
# ==========================================
def run_tests():
    test_cases = [
        {
            "name": "Empty Input Structure",
            "input": [],
            "expected_indices": [],
        },
        {
            "name": "Smallest Permitted Non-Empty Input",
            "input": [42],
            "expected_indices": [0],
        },
        {
            "name": "All Elements Equal (Disconnected Increasing Steps)",
            "input": [7, 7, 7, 7],
            "expected_indices": [0],  # All have length 1; index [0] is lexicographically smallest
        },
        {
            "name": "Strictly Decreasing Structure",
            "input": [5, 4, 3, 2, 1],
            "expected_indices": [0],  # Length 1; index [0] is lexicographically smallest
        },
        {
            "name": "Multiple Maximum Subsequences (Tie-Breaking Test)",
            "input": [3, 1, 4, 2],
            # Increasing sequences of max length 2:
            # [3, 4] -> indices [0, 2]
            # [1, 4] -> indices [1, 2]
            # [1, 2] -> indices [1, 3]
            # Lexicographically smallest index path is [0, 2]
            "expected_indices": [0, 2],
        },
        {
            "name": "Standard Route Test",
            "input": [10, 22, 9, 33, 21, 50, 41, 60, 80],
            "expected_indices": [0, 1, 3, 5, 7, 8],
        },
    ]

    all_passed = True
    for test in test_cases:
        result = get_lexicographically_smallest_lis_indices(test["input"])
        passed = result == test["expected_indices"]
        all_passed = all_passed and passed
        status = "PASSED" if passed else "FAILED"
        print(f"[{status}] {test['name']}")
        print(f"  Input: {test['input']}")
        print(f"  Result Indices:   {result}")
        print(f"  Expected Indices: {test['expected_indices']}\n")

    assert all_passed, "Some tests failed!"


if __name__ == "__main__":
    run_tests()