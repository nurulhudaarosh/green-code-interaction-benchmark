import sys
import bisect

def weighted_interval_scheduling(jobs):
    """
    Find maximum profit subset of non-overlapping jobs.
    
    Args:
        jobs: List of (start, finish, profit) tuples
        
    Returns:
        Tuple of (max_profit, list_of_job_indices) where list_of_job_indices
        are the 0-based indices in the original input order
    """
    if not jobs:
        return (0, [])
    
    n = len(jobs)
    
    # Sort jobs by finish time, then by start time, then by original index for deterministic tie-breaking
    # We need to track original indices
    jobs_with_idx = [(start, finish, profit, idx) for idx, (start, finish, profit) in enumerate(jobs)]
    jobs_with_idx.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Create arrays for sorted jobs
    sorted_starts = [x[0] for x in jobs_with_idx]
    sorted_finishes = [x[1] for x in jobs_with_idx]
    sorted_profits = [x[2] for x in jobs_with_idx]
    sorted_orig_idx = [x[3] for x in jobs_with_idx]
    
    # DP arrays
    dp_profit = [0] * (n + 1)  # dp[i] = max profit using first i jobs (sorted order)
    dp_choice = [None] * (n + 1)  # store choice for reconstruction
    dp_profit[0] = 0
    dp_choice[0] = -1  # sentinel
    
    # For each job in sorted order (1-indexed in DP)
    for i in range(1, n + 1):
        # Binary search for the last job that finishes <= start of job i-1
        start_time = sorted_starts[i - 1]
        # Find rightmost job with finish <= start_time
        p = bisect.bisect_right(sorted_finishes, start_time, 0, i - 1)
        # p is the count of jobs that finish <= start_time (0-indexed count)
        
        # Option 1: exclude current job
        exclude_profit = dp_profit[i - 1]
        exclude_choice = dp_choice[i - 1]
        
        # Option 2: include current job
        include_profit = sorted_profits[i - 1] + dp_profit[p]
        
        if include_profit > exclude_profit:
            # Include current job
            dp_profit[i] = include_profit
            # Store choice: include this job, and follow the choice from p
            dp_choice[i] = (i - 1, p)  # (current_job_index_in_sorted, previous_choice_state)
        else:
            # Exclude current job
            dp_profit[i] = exclude_profit
            dp_choice[i] = dp_choice[i - 1] if exclude_choice != -1 else -1
    
    # Reconstruct the optimal set of jobs
    selected_orig_indices = []
    i = n
    while i > 0:
        choice = dp_choice[i]
        if choice == -1:
            break
        if isinstance(choice, tuple):
            # We included a job
            job_idx_in_sorted, prev_state = choice
            selected_orig_indices.append(sorted_orig_idx[job_idx_in_sorted])
            i = prev_state
        else:
            # This should not happen if we set up correctly
            break
    
    # Return selected jobs in original index order (ascending)
    selected_orig_indices.sort()
    return (dp_profit[n], selected_orig_indices)


def main():
    # Read input
    # Format: First line contains number of jobs n
    # Next n lines: start finish profit
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    n = int(data[0])
    jobs = []
    idx = 1
    for _ in range(n):
        start = int(data[idx])
        finish = int(data[idx + 1])
        profit = int(data[idx + 2])
        jobs.append((start, finish, profit))
        idx += 3
    
    max_profit, selected_indices = weighted_interval_scheduling(jobs)
    
    # Output format: first line max profit, second line selected indices (space-separated)
    print(max_profit)
    if selected_indices:
        print(' '.join(str(i) for i in selected_indices))
    else:
        print()  # empty line for no jobs selected


if __name__ == "__main__":
    main()