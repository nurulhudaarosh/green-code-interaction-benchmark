from bisect import bisect_right
from typing import List, Tuple, Dict, Any, Union

def maximize_job_profit(
    jobs: List[Tuple[int, int, int]], 
    include_summary: bool = False
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, int]]]:
    """
    Finds a non-overlapping subset of jobs maximizing total profit.
    
    Args:
        jobs: List of tuples (start_time, finish_time, profit)
        include_summary: If True, returns an additional dictionary containing
                         a deterministic summary of computational operations.
                         
    Returns:
        If include_summary=False: (max_profit, selected_indices)
        If include_summary=True:  (max_profit, selected_indices, operation_summary)
    """
    if not jobs:
        summary = {
            "total_jobs": 0,
            "binary_search_steps": 0,
            "tie_breakers_evaluated": 0,
            "jobs_included_in_optimal": 0
        }
        return (0, [], summary) if include_summary else (0, [])

    # Index each job with its original position: (start, finish, profit, original_index)
    indexed_jobs = [
        (start, finish, profit, idx) 
        for idx, (start, finish, profit) in enumerate(jobs)
    ]
    
    # Sort by finish time ascending. Secondary keys ensure deterministic binary searching.
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[2], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # dp[i] stores (max_profit, selected_original_indices) for the first i sorted jobs
    dp = [(0, [])] * (n + 1)
    
    tie_breakers_count = 0
    
    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i - 1]
        
        # Binary search for the latest compatible job (F_j <= S_i)
        pred_idx = bisect_right(finish_times, start, hi=i - 1)
        
        # Option 1: Exclude job
        profit_exclude, indices_exclude = dp[i - 1]
        
        # Option 2: Include job
        profit_pred, indices_pred = dp[pred_idx]
        profit_include = profit_pred + profit
        indices_include = sorted(indices_pred + [orig_idx])
        
        # Select best decision
        if profit_include > profit_exclude:
            dp[i] = (profit_include, indices_include)
        elif profit_exclude > profit_include:
            dp[i] = (profit_exclude, indices_exclude)
        else:
            # Profit tie detected: evaluate lexicographical index order
            tie_breakers_count += 1
            if indices_include < indices_exclude:
                dp[i] = (profit_include, indices_include)
            else:
                dp[i] = (profit_exclude, indices_exclude)
                
    max_profit, selected_indices = dp[n]
    
    if include_summary:
        operation_summary = {
            "total_jobs": n,
            "binary_search_steps": n,
            "tie_breakers_evaluated": tie_breakers_count,
            "jobs_included_in_optimal": len(selected_indices)
        }
        return max_profit, selected_indices, operation_summary
        
    return max_profit, selected_indices


# Verification & Demonstration
if __name__ == "__main__":
    sample_jobs = [
        (1, 3, 50),
        (2, 4, 10),
        (3, 5, 40),
        (3, 6, 70)
    ]
    
    # Default call (Backward Compatible)
    result_standard = maximize_job_profit(sample_jobs)
    print("Standard Output:", result_standard)
    
    # Call with operation summary feature enabled
    max_p, indices, summary = maximize_job_profit(sample_jobs, include_summary=True)
    print(f"\nMax Profit: {max_p}")
    print(f"Selected Indices: {indices}")
    print("Operation Summary:", summary)