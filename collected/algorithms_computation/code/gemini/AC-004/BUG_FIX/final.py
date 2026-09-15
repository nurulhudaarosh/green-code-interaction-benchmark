from bisect import bisect_right
from typing import List, Tuple, Any

def max_profit_job_scheduling(jobs: List[Tuple[Any, Any, Any]]) -> Tuple[float, List[int]]:
    """
    Finds the non-overlapping subset of jobs with maximum profit,
    breaking ties deterministically by selecting the lexicographically smallest
    sequence of original 0-based job indices.
    """
    if not jobs:
        return 0, []

    # Store original 0-based index: (start, finish, profit, original_index)
    indexed_jobs = [(job[0], job[1], job[2], i) for i, job in enumerate(jobs)]
    
    # Primary sort: finish time ascending
    # Secondary sort: original index ascending
    indexed_jobs.sort(key=lambda x: (x[1], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # dp[i] stores (max_profit, lexicographically_smallest_path_indices)
    # considering a subset of the first i sorted jobs.
    dp = [(0, [])] * (n + 1)

    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i - 1]
        
        # 1. Option: Exclude job i
        best_profit, best_path = dp[i - 1]
        
        # 2. Binary search for ALL compatible predecessors ending <= start
        pred_hi = bisect_right(finish_times, start, hi=i - 1)
        
        # Check compatible predecessor states to find the best profit & path when INCLUDING job i
        for k in range(pred_hi, -1, -1):
            pred_profit, pred_path = dp[k]
            
            # If the predecessor profit is smaller than the max compatible profit found so far,
            # earlier predecessors will have <= profit, so we can break early if we track max_pred.
            cand_profit = pred_profit + profit
            cand_path = sorted(pred_path + [orig_idx])
            
            if cand_profit > best_profit:
                best_profit = cand_profit
                best_path = cand_path
            elif cand_profit == best_profit:
                if cand_path < best_path or not best_path:
                    best_path = cand_path

        dp[i] = (best_profit, best_path)

    return dp[n]


# --- Verification of Fix ---
if __name__ == "__main__":
    # Test case demonstrating the defect
    defect_jobs = [
        (1, 2, 10), # Index 0
        (1, 2, 10), # Index 1
        (2, 3, 5)   # Index 2
    ]

    profit, indices = max_profit_job_scheduling(defect_jobs)
    print(f"Max Profit: {profit}")
    print(f"Selected Indices: {indices}")
    # Output will strictly be [0, 2], resolving the tie-breaking bug.