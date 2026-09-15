from bisect import bisect_right
from typing import List, Tuple, Any

def max_profit_job_scheduling(jobs: List[Tuple[Any, Any, Any]]) -> Tuple[float, List[int]]:
    """
    Finds the non-overlapping subset of jobs with maximum profit.
    
    Args:
        jobs: List of tuples (start, finish, profit)
        
    Returns:
        Tuple of (max_profit, list_of_original_indices)
    """
    if not jobs:
        return 0, []

    # Store original indices along with job details
    # Form: (start, finish, profit, original_index)
    indexed_jobs = [(job[0], job[1], job[2], i) for i, job in enumerate(jobs)]
    
    # Sort primarily by finish time, secondarily by original index
    indexed_jobs.sort(key=lambda x: (x[1], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # dp[i] stores (max_profit, sorted_list_of_original_indices) for the first i jobs
    dp = [(0, [])] * (n + 1)

    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i - 1]
        
        # Binary search for the latest compatible job (finish_time <= start)
        pred_idx = bisect_right(finish_times, start, hi=i - 1)
        
        # Option 1: Exclude the current job
        profit_exclude, path_exclude = dp[i - 1]
        
        # Option 2: Include the current job
        profit_pred, path_pred = dp[pred_idx]
        profit_include = profit_pred + profit
        
        # Form the sorted list of indices for Option 2
        path_include = sorted(path_pred + [orig_idx])
        
        # Compare and select (tie-breaking by smaller original-index sequence)
        if profit_include > profit_exclude:
            dp[i] = (profit_include, path_include)
        elif profit_exclude > profit_include:
            dp[i] = (profit_exclude, path_exclude)
        else:
            # Profits are equal; break tie lexicographically
            if path_include < path_exclude:
                dp[i] = (profit_include, path_include)
            else:
                dp[i] = (profit_exclude, path_exclude)

    return dp[n]


# Example usage
if __name__ == "__main__":
    # Jobs represented as (start, finish, profit)
    example_jobs = [
        (1, 3, 50),
        (2, 4, 10),
        (3, 5, 20),
        (3, 6, 70)
    ]

    max_p, selected = max_profit_job_scheduling(example_jobs)
    print(f"Maximum Profit: {max_p}")
    print(f"Selected Job Indices: {selected}")