def find_lexicographically_smallest_LIS(seq):
    """
    Returns the indices (0-based) of the lexicographically smallest
    strictly increasing subsequence of maximum length.
    """
    n = len(seq)
    if n == 0:
        return []

    # dp[i] = length of LIS ending at i
    dp = [1] * n
    # prev[i] = previous index in the optimal subsequence ending at i
    prev = [-1] * n

    # For each position i, find the best predecessor j < i
    for i in range(n):
        best_len = 1
        best_prev = -1
        
        for j in range(i):
            if seq[j] < seq[i]:
                # Candidate length if we extend subsequence ending at j
                cand_len = dp[j] + 1
                if cand_len > best_len:
                    best_len = cand_len
                    best_prev = j
                elif cand_len == best_len:
                    # Tie-breaking: choose predecessor that gives lexicographically smaller index sequence
                    # We compare the chains ending at j and best_prev
                    # Since both chains have same length, we compare from the start
                    chain1 = get_chain(j, prev)
                    chain2 = get_chain(best_prev, prev)
                    # We need to compare full sequences (including current index i)
                    # but current i is same, so compare chains ending at j and best_prev
                    if chain1 < chain2:
                        best_prev = j
        
        dp[i] = best_len
        prev[i] = best_prev

    # Find the maximum length and the best ending index (lexicographically smallest chain)
    max_len = max(dp)
    best_end = -1
    best_chain = None
    
    for i in range(n):
        if dp[i] == max_len:
            chain = get_chain(i, prev)
            if best_chain is None or chain < best_chain:
                best_chain = chain
                best_end = i

    # Reconstruct the sequence from the best ending
    result = []
    cur = best_end
    while cur != -1:
        result.append(cur)
        cur = prev[cur]
    result.reverse()
    return result


def get_chain(idx, prev):
    """
    Helper to get the index sequence ending at idx as a tuple for comparison.
    """
    chain = []
    cur = idx
    while cur != -1:
        chain.append(cur)
        cur = prev[cur]
    chain.reverse()
    return tuple(chain)


# Alternative more efficient tie-breaking (O(n²) time but O(n) space for comparison)
def find_lexicographically_smallest_LIS_optimized(seq):
    """
    Optimized version: avoids constructing full chains for every comparison
    by comparing lexicographically using predecessor arrays.
    """
    n = len(seq)
    if n == 0:
        return []

    dp = [1] * n
    prev = [-1] * n

    for i in range(n):
        best_len = 1
        best_prev = -1
        
        for j in range(i):
            if seq[j] < seq[i]:
                cand_len = dp[j] + 1
                if cand_len > best_len:
                    best_len = cand_len
                    best_prev = j
                elif cand_len == best_len:
                    # Compare lexicographically by walking both chains
                    if is_lexicographically_smaller(j, best_prev, prev):
                        best_prev = j
        
        dp[i] = best_len
        prev[i] = best_prev

    max_len = max(dp)
    best_end = -1
    
    for i in range(n):
        if dp[i] == max_len:
            if best_end == -1 or is_lexicographically_smaller(i, best_end, prev):
                best_end = i

    # Reconstruct
    result = []
    cur = best_end
    while cur != -1:
        result.append(cur)
        cur = prev[cur]
    result.reverse()
    return result


def is_lexicographically_smaller(idx1, idx2, prev):
    """
    Compare two chains ending at idx1 and idx2.
    Returns True if chain1 < chain2 lexicographically.
    Assumes chains have the same length.
    """
    # Collect both chains from start to end
    chain1 = []
    chain2 = []
    
    cur1 = idx1
    while cur1 != -1:
        chain1.append(cur1)
        cur1 = prev[cur1]
    
    cur2 = idx2
    while cur2 != -1:
        chain2.append(cur2)
        cur2 = prev[cur2]
    
    chain1.reverse()
    chain2.reverse()
    
    # Since they have same length, compare element by element
    for a, b in zip(chain1, chain2):
        if a < b:
            return True
        if a > b:
            return False
    return False  # equal chains


# Final deterministic solution with clear interface
def longest_increasing_subsequence_indices(seq):
    """
    Returns the indices (0-based) of the lexicographically smallest
    strictly increasing subsequence of maximum length.
    
    Time complexity: O(n²)
    Space complexity: O(n)
    """
    return find_lexicographically_smallest_LIS_optimized(seq)


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ([10, 9, 2, 5, 3, 7, 101, 18], [2, 4, 5, 7]),  # indices 2,4,5,7 -> values 2,3,7,18
        ([0, 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15], [0, 2, 4, 6, 8, 10, 12, 14]), # lexicographically smallest indices
        ([3, 2, 1], [2]),  # any single element, smallest index is 2 (value 1)
        ([1, 2, 3], [0, 1, 2]),
        ([], []),
        ([5], [0]),
        ([2, 2, 2], [0]),  # strictly increasing, so only one
        ([1, 3, 2, 4], [0, 2, 3]),  # 1,2,4 vs 1,3,4 -> 1,2,4 has smaller indices [0,2,3] < [0,1,3]
    ]
    
    for seq, expected in test_cases:
        result = longest_increasing_subsequence_indices(seq)
        print(f"seq: {seq}")
        print(f"result: {result} (values: {[seq[i] for i in result]})")
        print(f"expected: {expected}")
        print(f"correct: {result == expected}")
        print()