from bisect import bisect_right
from typing import List, Tuple, Any

def maximize_job_profit(jobs: List[Tuple[int, int, int]]) -> Tuple[int, List[int]]:
    """
    Finds a non-overlapping subset of jobs maximizing total profit.
    
    Args:
        jobs: List of tuples (start_time, finish_time, profit)
        
    Returns:
        Tuple containing (max_profit, list_of_original_indices)
    """
    if not jobs:
        return 0, []

    # Store original 0-based index with each job: (start, finish, profit, original_index)
    indexed_jobs = [
        (start, finish, profit, idx) 
        for idx, (start, finish, profit) in enumerate(jobs)
    ]
    
    # Sort primarily by finish time. Use start, profit, and orig index as secondary keys.
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[2], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # dp[i] stores (max_profit, selected_original_indices) for the first i sorted jobs
    dp = [(0, [])] * (n + 1)
    
    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i - 1]
        
        # Binary search for the latest job that finishes <= start time of current job
        # bisect_right finds insertion point for 'start', so index - 1 is the predecessor
        pred_idx = bisect_right(finish_times, start, hi=i - 1)
        
        # Option 1: Exclude the current job
        profit_exclude, indices_exclude = dp[i - 1]
        
        # Option 2: Include the current job
        profit_pred, indices_pred = dp[pred_idx]
        profit_include = profit_pred + profit
        indices_include = sorted(indices_pred + [orig_idx])
        
        # Decide between including or excluding the job (with tie-breaking)
        if profit_include > profit_exclude:
            dp[i] = (profit_include, indices_include)
        elif profit_exclude > profit_include:
            dp[i] = (profit_exclude, indices_exclude)
        else:
            # Profits are equal: pick the lexicographically smaller list of indices
            if indices_include < indices_exclude:
                dp[i] = (profit_include, indices_include)
            else:
                dp[i] = (profit_exclude, indices_exclude)
                
    return dp[n]


# Example Usage
if __name__ == "__main__":
    # Jobs represented as (Start, Finish, Profit)
    sample_jobs = [
        (1, 3, 50),
        (2, 4, 10),
        (3, 5, 40),
        (3, 6, 70)
    ]
    
    max_profit, selected_jobs = maximize_job_profit(sample_jobs)
    print(f"Maximum Profit: {max_profit}")
    print(f"Selected Job Indices: {selected_jobs}")