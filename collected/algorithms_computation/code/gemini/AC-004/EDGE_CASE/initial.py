from bisect import bisect_right

def max_profit_weighted_interval_scheduling(jobs):
    """
    Finds a non-overlapping subset of jobs maximizing profit.
    
    Parameters:
        jobs (list of tuples): Each element is (start_time, finish_time, profit)
        
    Returns:
        tuple: (max_profit, selected_original_indices)
    """
    if not jobs:
        return 0, []

    # Store jobs with their original indices: (start, finish, profit, original_index)
    indexed_jobs = [
        (s, f, p, i) for i, (s, f, p) in enumerate(jobs)
    ]
    
    # Sort primarily by finish time, secondarily by start time, then original index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # dp[i] stores (max_profit, tuple_of_selected_original_indices) for first i jobs
    dp = [(0, ())] * (n + 1)
    
    for i in range(1, n + 1):
        s_i, f_i, p_i, idx_i = indexed_jobs[i - 1]
        
        # Binary search for the latest non-overlapping job (finish_time <= start_time)
        pred = bisect_right(finish_times, s_i, hi=i - 1) - 1
        
        # Option 1: Exclude job i-1
        excl_profit, excl_indices = dp[i - 1]
        
        # Option 2: Include job i-1
        pred_profit, pred_indices = dp[pred + 1]
        incl_profit = pred_profit + p_i
        
        # Keep original indices sorted for lexicographical comparison
        incl_indices = tuple(sorted(pred_indices + (idx_i,)))
        
        # Deterministic choice: Maximize profit, break ties via lexicographical index order
        if incl_profit > excl_profit:
            dp[i] = (incl_profit, incl_indices)
        elif excl_profit > incl_profit:
            dp[i] = (excl_profit, excl_indices)
        else:
            # Equal profit: select the lexicographically smaller sequence of original indices
            dp[i] = min((excl_profit, excl_indices), (incl_profit, incl_indices), key=lambda x: x[1])

    max_profit, selected_indices = dp[n]
    return max_profit, list(selected_indices)


# Example Usage
if __name__ == "__main__":
    # Jobs represented as (start, finish, profit)
    sample_jobs = [
        (1, 3, 50),  # Job 0
        (2, 5, 20),  # Job 1
        (3, 6, 50),  # Job 2
        (6, 8, 30)   # Job 3
    ]

    total_profit, chosen_jobs = max_profit_weighted_interval_scheduling(sample_jobs)
    print(f"Maximum Profit: {total_profit}")
    print(f"Selected Job Indices: {chosen_jobs}")