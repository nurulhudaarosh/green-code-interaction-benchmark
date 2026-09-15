import sys
import bisect

def weighted_interval_scheduling(jobs):
    """
    Solve weighted interval scheduling with tie-breaking by original index.
    
    Args:
        jobs: List of tuples (start, finish, profit)
    
    Returns:
        tuple: (max_profit, list_of_selected_job_indices)
               where indices are 0-based original positions
    """
    if not jobs:
        return 0, []
    
    n = len(jobs)
    
    # Store original indices with jobs
    indexed_jobs = [(start, finish, profit, idx) for idx, (start, finish, profit) in enumerate(jobs)]
    
    # Sort by finish time (primary), start time (secondary), then original index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Extract sorted data
    starts = [job[0] for job in indexed_jobs]
    finishes = [job[1] for job in indexed_jobs]
    profits = [job[2] for job in indexed_jobs]
    orig_indices = [job[3] for job in indexed_jobs]
    
    # DP arrays
    dp = [0] * (n + 1)  # dp[i] = max profit using first i jobs (sorted order)
    selected = [[] for _ in range(n + 1)]  # selected jobs for each dp state
    
    for i in range(1, n + 1):
        # Find the latest job that finishes before or at the start of job i-1
        # Since jobs touching at endpoints are compatible, we use bisect_right
        j = bisect.bisect_right(finishes, starts[i-1], 0, i-1)
        
        # Option 1: Exclude current job
        exclude_profit = dp[i-1]
        exclude_selected = selected[i-1]
        
        # Option 2: Include current job
        include_profit = dp[j] + profits[i-1]
        include_selected = selected[j] + [orig_indices[i-1]]
        
        # Choose the better option
        if include_profit > exclude_profit:
            dp[i] = include_profit
            selected[i] = include_selected
        elif include_profit < exclude_profit:
            dp[i] = exclude_profit
            selected[i] = exclude_selected
        else:
            # Tie: choose lexicographically smaller sequence of original indices
            # Compare as tuples for lexicographic order
            include_tuple = tuple(include_selected)
            exclude_tuple = tuple(exclude_selected)
            if include_tuple < exclude_tuple:
                dp[i] = include_profit
                selected[i] = include_selected
            else:
                dp[i] = exclude_profit
                selected[i] = exclude_selected
    
    return dp[n], selected[n]


def solve():
    """
    Read input from stdin and output the result.
    Input format:
    First line: n (number of jobs)
    Next n lines: start finish profit (space-separated integers)
    """
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
    
    # Output: max profit on first line, then selected indices on second line
    print(max_profit)
    print(' '.join(map(str, selected_indices)))


if __name__ == "__main__":
    solve()