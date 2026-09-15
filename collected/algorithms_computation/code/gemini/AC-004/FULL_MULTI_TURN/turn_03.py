from bisect import bisect_right

def job_scheduling(jobs, return_summary=False):
    """
    Solves the Weighted Interval Scheduling Problem with tie-breaking and summary tracking.
    
    Parameters:
    jobs (list of tuples/lists): Each element is (start, finish, profit)
    return_summary (bool): If True, returns an additional operation_summary dict.
    
    Returns:
    tuple: (max_profit, selected_indices) if return_summary=False
           (max_profit, selected_indices, operation_summary) if return_summary=True
    """
    if not jobs:
        summary = {
            "total_jobs": 0,
            "binary_searches": 0,
            "dp_decisions": 0,
            "tie_breaks": 0
        }
        return (0, [], summary) if return_summary else (0, [])

    # Metrics counter
    binary_searches = 0
    dp_decisions = 0
    tie_breaks = 0

    # Attach original index to each job: (start, finish, profit, original_index)
    indexed_jobs = [
        (s, f, p, i) for i, (s, f, p) in enumerate(jobs)
    ]
    
    # Deterministic sorting: finish time, start time, original index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # DP table stores tuples: (profit, original_indices_list)
    dp = [(0, [])] * (n + 1)
    
    for i in range(1, n + 1):
        s, f, p, orig_idx = indexed_jobs[i - 1]
        
        # Binary search for predecessor job finish_time <= start_time s
        pred_idx = bisect_right(finish_times, s, hi=i - 1)
        binary_searches += 1
        
        # Option 1: Include current job
        prev_profit, prev_seq = dp[pred_idx]
        incl_profit = prev_profit + p
        incl_seq = sorted(prev_seq + [orig_idx])
        
        # Option 2: Exclude current job
        excl_profit, excl_seq = dp[i - 1]
        
        dp_decisions += 1
        
        # State decision with tie-breaking
        if incl_profit > excl_profit:
            dp[i] = (incl_profit, incl_seq)
        elif excl_profit > incl_profit:
            dp[i] = (excl_profit, excl_seq)
        else:
            tie_breaks += 1
            dp[i] = (incl_profit, min(incl_seq, excl_seq))
            
    max_profit, selected_indices = dp[n]
    
    if return_summary:
        operation_summary = {
            "total_jobs": n,
            "binary_searches": binary_searches,
            "dp_decisions": dp_decisions,
            "tie_breaks": tie_breaks
        }
        return max_profit, selected_indices, operation_summary
    
    return max_profit, selected_indices


# --- Example Usage ---
if __name__ == "__main__":
    sample_jobs = [
        (1, 3, 50),  # Job 0
        (2, 4, 10),  # Job 1
        (3, 5, 40),  # Job 2
        (3, 6, 70)   # Job 3
    ]
    
    # Standard original call
    result = job_scheduling(sample_jobs)
    print("Default Output:", result)
    
    # Call with feature enabled
    profit, indices, summary = job_scheduling(sample_jobs, return_summary=True)
    print("\nFeature Output:")
    print(f"Max Profit: {profit}")
    print(f"Selected Indices: {indices}")
    print(f"Operation Summary: {summary}")