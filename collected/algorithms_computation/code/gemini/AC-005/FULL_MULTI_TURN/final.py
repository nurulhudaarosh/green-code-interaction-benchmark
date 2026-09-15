def run_tests():
    # Test 1: Empty structure (smallest permitted input)
    assert lexicographically_smallest_lis_indices([]) == []

    # Test 2: Single element
    assert lexicographically_smallest_lis_indices([42]) == [0]

    # Test 3: Strictly decreasing array (no extensions possible)
    assert lexicographically_smallest_lis_indices([5, 4, 3, 2, 1]) == [0]

    # Test 4: All equal elements (no strict increase possible)
    assert lexicographically_smallest_lis_indices([7, 7, 7, 7]) == [0]

    # Test 5: Lexicographical tie-breaking among equal-value candidates
    # arr = [10, 20, 1, 30] -> LIS length 3: [10, 20, 30] (indices [0, 1, 3])
    assert lexicographically_smallest_lis_indices([10, 20, 1, 30]) == [0, 1, 3]

    # Test 6: Negative numbers and mixed values
    # [-5, -10, 0, -3, 5] -> optimal indices [1, 3, 4] (values [-10, -3, 5])
    assert lexicographically_smallest_lis_indices([-5, -10, 0, -3, 5]) == [1, 3, 4]

    # Test 7: include_summary flag functionality on empty input
    res_empty = lexicographically_smallest_lis_indices([], include_summary=True)
    assert res_empty["indices"] == []
    assert res_empty["operation_summary"] == {
        "comparisons": 0,
        "dp_updates": 0,
        "reconstruction_steps": 0
    }

    # Test 8: include_summary flag functionality on valid array
    res_summary = lexicographically_smallest_lis_indices([10, 20, 1, 30], include_summary=True)
    assert res_summary["indices"] == [0, 1, 3]
    assert "comparisons" in res_summary["operation_summary"]
    assert "dp_updates" in res_summary["operation_summary"]

    print("All tests passed successfully!")


if __name__ == "__main__":
    run_tests()