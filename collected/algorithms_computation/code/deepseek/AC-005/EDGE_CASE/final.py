def longest_increasing_subsequence_indices(a):
    """
    Returns the lexicographically smallest index sequence among all
    longest strictly increasing subsequences of array a.
    
    Args:
        a: list of integers (can be empty)
    
    Returns:
        list of 0-based indices
    """
    n = len(a)
    
    # Edge case: empty sequence
    if n == 0:
        return []
    
    # dp[i] = length of LIS ending at i
    dp = [1] * n
    
    # seq[i] = tuple of indices for the best sequence ending at i
    seq = [None] * n
    
    for i in range(n):
        # Base: sequence of just [i]
        seq[i] = (i,)
        
        # Try all previous indices
        for j in range(i):
            if a[j] < a[i]:  # strictly increasing
                cand_len = dp[j] + 1
                cand_seq = seq[j] + (i,)
                
                if cand_len > dp[i]:
                    # Better length
                    dp[i] = cand_len
                    seq[i] = cand_seq
                elif cand_len == dp[i]:
                    # Same length: keep lexicographically smaller
                    if cand_seq < seq[i]:
                        seq[i] = cand_seq
    
    # Find the maximum length
    best_len = max(dp)
    
    # Among all indices with that length, pick lexicographically smallest sequence
    candidates = [i for i in range(n) if dp[i] == best_len]
    best_seq = min(seq[i] for i in candidates)
    
    return list(best_seq)


# ============ TEST CASES ============

def test_lis():
    """Run test cases to verify correctness including edge cases."""
    
    # Test 1: Empty sequence
    assert longest_increasing_subsequence_indices([]) == []
    
    # Test 2: Single element
    assert longest_increasing_subsequence_indices([5]) == [0]
    
    # Test 3: Strictly increasing
    assert longest_increasing_subsequence_indices([1, 2, 3]) == [0, 1, 2]
    
    # Test 4: Strictly decreasing
    # All length-1 subsequences are optimal; lexicographically smallest is [0]
    assert longest_increasing_subsequence_indices([3, 2, 1]) == [0]
    
    # Test 5: All equal
    assert longest_increasing_subsequence_indices([5, 5, 5]) == [0]
    
    # Test 6: Duplicates with increasing elsewhere
    # [1, 2, 2, 3] -> LIS length 3, options: [0,1,3] and [0,2,3]
    # Lexicographically smaller: [0,1,3] vs [0,2,3] -> [0,1,3]
    assert longest_increasing_subsequence_indices([1, 2, 2, 3]) == [0, 1, 3]
    
    # Test 7: Multiple optimal with different starting points
    # [2, 1, 3] -> LIS length 2: [0,2] and [1,2]; lexicographically [0,2] < [1,2]
    assert longest_increasing_subsequence_indices([2, 1, 3]) == [0, 2]
    
    # Test 8: Complex tie-breaking
    # [1, 3, 2, 4] -> LIS length 3: [0,1,3] and [0,2,3]; [0,1,3] < [0,2,3]
    assert longest_increasing_subsequence_indices([1, 3, 2, 4]) == [0, 1, 3]
    
    # Test 9: Negative numbers
    assert longest_increasing_subsequence_indices([-1, -2, -3, 0]) == [0, 3]  # [-1,0] or [-2,0] or [-3,0]; lexicographically [0,3]
    
    # Test 10: More complex tie
    # [0, 1, 0, 2] -> LIS length 3: [0,1,3] and [2,? no] wait: [0,1,3] is length 3, [0,2,3] is also length 3? 
    # Check: a[0]=0, a[2]=0 (not strictly), so [0,2,3] invalid. Only [0,1,3].
    assert longest_increasing_subsequence_indices([0, 1, 0, 2]) == [0, 1, 3]
    
    # Test 11: Another tie
    # [2, 3, 1, 4] -> LIS length 3: [0,1,3] and [2,?] no, [2] can't go to 4? a[2]=1 < a[3]=4 -> [2,3] length 2, so only [0,1,3]
    # Actually [0,1,3] = [2,3,4], length 3. Also [0,?] maybe [0,?] only that.
    assert longest_increasing_subsequence_indices([2, 3, 1, 4]) == [0, 1, 3]
    
    # Test 12: More interesting tie-breaking where both have same length and different indices
    # [1, 2, 0, 3] -> LIS length 3: [0,1,3] (1,2,3) and [2,?] [2,3] length 2 only. So only [0,1,3]
    # Let's create: [1, 2, 3, 0] -> LIS length 3: [0,1,2] only.
    # Need case where two sequences same length: [1, 2, 0, 3, 4] -> [0,1,3,4] and [2,3,4]; lexicographically [0,1,3,4] < [2,3,4]
    assert longest_increasing_subsequence_indices([1, 2, 0, 3, 4]) == [0, 1, 3, 4]
    
    # Test 13: Another: [3, 1, 2, 4] -> LIS length 3: [1,2,3] indices [1,2,3] or [0,?] [0,?] cannot since 3>1,2,4? Actually [0,?] only [0] then nothing after? 3<4 so [0,3] length 2. So only [1,2,3]
    assert longest_increasing_subsequence_indices([3, 1, 2, 4]) == [1, 2, 3]
    
    # Test 14: Empty disconnected? Not possible; all indices are connected by "less than" relation.
    
    print("All tests passed!")


if __name__ == "__main__":
    test_lis()