from bisect import bisect_right

def job_scheduling(jobs):
    """
    Solves the Weighted Interval Scheduling Problem.
    
    Parameters:
    jobs (list of tuples/lists): Each element is (start, finish, profit)
    
    Returns:
    tuple: (max_profit, list_of_selected_original_indices)
    """
    if not jobs:
        return 0, []

    # Attach original index to each job: (start, finish, profit, original_index)
    indexed_jobs = [
        (s, f, p, i) for i, (s, f, p) in enumerate(jobs)
    ]
    
    # Sort primarily by finish time, secondarily by start time and original index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # DP table stores tuples: (profit, original_indices_list)
    # dp[i] corresponds to the optimal solution for the first i jobs
    dp = [(0, [])] * (n + 1)
    
    for i in range(1, n + 1):
        s, f, p, orig_idx = indexed_jobs[i - 1]
        
        # Find latest non-overlapping job using binary search
        # We search for the rightmost job with finish_time <= start_time s
        pred_idx = bisect_right(finish_times, s, hi=i - 1)
        
        # Option 1: Include current job
        prev_profit, prev_seq = dp[pred_idx]
        incl_profit = prev_profit + p
        # Form new sequence sorted by original index
        incl_seq = sorted(prev_seq + [orig_idx])
        
        # Option 2: Exclude current job
        excl_profit, excl_seq = dp[i - 1]
        
        # Select best option: maximize profit, then minimize index sequence lexicographically
        if incl_profit > excl_profit:
            dp[i] = (incl_profit, incl_seq)
        elif excl_profit > incl_profit:
            dp[i] = (excl_profit, excl_seq)
        else:
            # Profits are equal -> lexicographical tie-break on job index sequences
            dp[i] = (incl_profit, min(incl_seq, excl_seq))
            
    return dp[n]

# --- Example Usage ---
if __name__ == "__main__":
    # Jobs represented as (start, finish, profit)
    sample_jobs = [
        (1, 3, 50),  # Job 0
        (2, 4, 10),  # Job 1
        (3, 5, 40),  # Job 2
        (3, 6, 70)   # Job 3
    ]
    
    max_profit, chosen_jobs = job_scheduling(sample_jobs)
    print(f"Maximum Profit: {max_profit}")
    print(f"Selected Job Original Indices: {chosen_jobs}")