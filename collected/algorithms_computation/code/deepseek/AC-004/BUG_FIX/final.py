import sys
import bisect

def solve_weighted_interval_scheduling(jobs):
    """
    Solve weighted interval scheduling with tie-breaking by smallest original index sequence.
    
    Args:
        jobs: List of tuples (start, finish, profit) for each job
    
    Returns:
        Tuple (max_profit, list of original indices in selected subset)
    """
    if not jobs:
        return 0, []
    
    # Add original indices to jobs for tie-breaking
    indexed_jobs = [(start, finish, profit, i) for i, (start, finish, profit) in enumerate(jobs)]
    
    # Sort by finish time, then by original index for deterministic ordering
    indexed_jobs.sort(key=lambda x: (x[1], x[3]))
    
    n = len(indexed_jobs)
    
    # Extract sorted finish times for binary search
    finish_times = [job[1] for job in indexed_jobs]
    
    # dp_profit[i] = maximum profit using first i jobs
    dp_profit = [0] * (n + 1)
    # dp_indices[i] = list of original indices (in selection order) for optimal solution
    dp_indices = [[] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i - 1]
        
        # Find the latest job that finishes <= this job's start time
        j = bisect.bisect_right(finish_times, start, 0, i - 1)
        
        # Option 1: Exclude current job
        exclude_profit = dp_profit[i - 1]
        exclude_indices = dp_indices[i - 1]
        
        # Option 2: Include current job
        include_profit = dp_profit[j] + profit
        include_indices = dp_indices[j] + [orig_idx]
        
        # Compare options: higher profit wins
        if include_profit > exclude_profit:
            dp_profit[i] = include_profit
            dp_indices[i] = include_indices
        elif exclude_profit > include_profit:
            dp_profit[i] = exclude_profit
            dp_indices[i] = exclude_indices
        else:
            # Tie: choose lexicographically smaller sequence of original indices
            # Compare directly (original order matters, not sorted)
            if include_indices < exclude_indices:
                dp_profit[i] = include_profit
                dp_indices[i] = include_indices
            else:
                dp_profit[i] = exclude_profit
                dp_indices[i] = exclude_indices
    
    return dp_profit[n], dp_indices[n]


def main():
    """Read input and output the result."""
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
    
    max_profit, selected_indices = solve_weighted_interval_scheduling(jobs)
    
    print(max_profit)
    print(' '.join(map(str, selected_indices)))


if __name__ == "__main__":
    main()