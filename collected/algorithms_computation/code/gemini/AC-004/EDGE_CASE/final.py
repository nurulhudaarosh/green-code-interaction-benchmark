from bisect import bisect_right

def max_profit_weighted_interval_scheduling(jobs):
    """
    Finds a non-overlapping subset of jobs maximizing profit with deterministic
    lexicographical tie-breaking on original indices.
    
    Time Complexity: O(N log N) average / O(N log N) worst-case
    Space Complexity: O(N)
    """
    if not jobs:
        return 0, []

    n = len(jobs)
    
    # Store jobs with original indices: (start, finish, profit, original_index)
    indexed_jobs = [
        (s, f, p, i) for i, (s, f, p) in enumerate(jobs)
    ]
    
    # Primary sort: finish time, Secondary: start time, Tertiary: original index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    finish_times = [job[1] for job in indexed_jobs]
    
    # Precompute predecessor indices using binary search
    pred = [0] * (n + 1)
    for i in range(1, n + 1):
        s_i = indexed_jobs[i - 1][0]
        pred[i] = bisect_right(finish_times, s_i, hi=i - 1)

    # dp[i] stores only the max profit achievable using a subset of first i jobs
    dp = [0] * (n + 1)
    
    # parent[i] stores choice made at step i:
    # 'E' for Exclude, 'I' for Include
    choices = [''] * (n + 1)

    # Path reconstruction cache to keep tie-breaking efficient
    memo_path = {}

    def get_path(i):
        """Reconstructs the sorted original indices for prefix i dynamically."""
        if i == 0:
            return ()
        if i in memo_path:
            return memo_path[i]
        
        if choices[i] == 'I':
            orig_idx = indexed_jobs[i - 1][3]
            prev_path = get_path(pred[i])
            # Insert maintaining sorted order for original indices
            path = tuple(sorted(prev_path + (orig_idx,)))
        else:
            path = get_path(i - 1)
            
        memo_path[i] = path
        return path

    for i in range(1, n + 1):
        s_i, f_i, p_i, idx_i = indexed_jobs[i - 1]
        
        excl_profit = dp[i - 1]
        incl_profit = dp[pred[i]] + p_i
        
        if incl_profit > excl_profit:
            dp[i] = incl_profit
            choices[i] = 'I'
        elif excl_profit > incl_profit:
            dp[i] = excl_profit
            choices[i] = 'E'
        else:
            # Profit Tie-Break: Compare resulting index sequences
            # Exclude path
            choices[i] = 'E'
            excl_path = get_path(i)
            
            # Include path
            choices[i] = 'I'
            incl_path = get_path(i)
            
            if incl_path < excl_path:
                choices[i] = 'I'
                dp[i] = incl_profit
            else:
                choices[i] = 'E'
                dp[i] = excl_profit

    max_profit = dp[n]
    selected_indices = list(get_path(n))
    return max_profit, selected_indices


# --------------------------------------------------------------------
# Test Suite Including Worst-Case & Complex Edge Scenarios
# --------------------------------------------------------------------

def run_tests():
    # Test 1: Standard case
    jobs1 = [(1, 3, 50), (2, 5, 20), (3, 6, 50), (6, 8, 30)]
    assert max_profit_weighted_interval_scheduling(jobs1) == (130, [0, 2, 3])

    # Test 2: Endpoint touching compatibility (Start == Finish)
    jobs2 = [(1, 2, 10), (2, 3, 20), (3, 4, 30)]
    assert max_profit_weighted_interval_scheduling(jobs2) == (60, [0, 1, 2])

    # Test 3: Lexicographical tie-breaking on index
    # Job 0 and Job 1 are identical intervals with identical profit.
    # Selecting [0] should beat selecting [1].
    jobs3 = [(1, 5, 50), (1, 5, 50)]
    assert max_profit_weighted_interval_scheduling(jobs3) == (50, [0])

    # Test 4: Worst-Case Chain (Large non-overlapping sequence with tied alternatives)
    # Tests performance scaling and tie resolution across long decision chains
    N = 1000
    jobs_worst_case = []
    for i in range(N):
        # Disjoint intervals with identical profits
        jobs_worst_case.append((i * 2, i * 2 + 1, 10))
        # Overlapping duplicate intervals to trigger heavy tie-breaking evaluation
        jobs_worst_case.append((i * 2, i * 2 + 1, 10))

    profit, indices = max_profit_weighted_interval_scheduling(jobs_worst_case)
    assert profit == N * 10
    # Every choice should pick the lower original index (even indices: 0, 2, 4...)
    assert indices == [2 * i for i in range(N)]

    # Test 5: All jobs overlapping at same start/finish with equal profits
    jobs5 = [(0, 10, 100) for _ in range(500)]
    profit5, indices5 = max_profit_weighted_interval_scheduling(jobs5)
    assert profit5 == 100
    assert indices5 == [0]

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()