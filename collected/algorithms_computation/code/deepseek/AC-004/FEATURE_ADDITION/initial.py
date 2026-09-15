import sys
import bisect

def solve_weighted_interval_scheduling(jobs):
    """
    Solve weighted interval scheduling with tie-breaking by original index.
    
    Args:
        jobs: List of tuples (start, finish, profit)
    
    Returns:
        Tuple of (max_profit, selected_indices) where selected_indices is a list
        of original indices (0-based) in sorted order by finish time.
    """
    if not jobs:
        return 0, []
    
    n = len(jobs)
    
    # Create jobs with original indices and sort by finish time
    # For ties in finish time, sort by start time (not required but deterministic)
    indexed_jobs = [(start, finish, profit, i) for i, (start, finish, profit) in enumerate(jobs)]
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    # Extract sorted data
    starts = [job[0] for job in indexed_jobs]
    finishes = [job[1] for job in indexed_jobs]
    profits = [job[2] for job in indexed_jobs]
    orig_indices = [job[3] for job in indexed_jobs]
    
    # DP arrays
    dp = [0] * n  # dp[i] = max profit considering jobs[0..i]
    selected = [[] for _ in range(n)]  # selected[i] = list of original indices for optimal subset
    
    # Base case
    dp[0] = profits[0]
    selected[0] = [orig_indices[0]]
    
    # Binary search helper: find rightmost job with finish <= start
    for i in range(1, n):
        # Option 1: exclude job i
        best_profit = dp[i-1]
        best_selected = selected[i-1][:]
        
        # Option 2: include job i
        # Find compatible predecessor
        j = bisect.bisect_right(finishes, starts[i]) - 1
        
        include_profit = profits[i]
        include_selected = [orig_indices[i]]
        
        if j >= 0:
            include_profit += dp[j]
            include_selected = selected[j][:] + [orig_indices[i]]
        
        # Choose better option
        if include_profit > best_profit:
            best_profit = include_profit
            best_selected = include_selected
        elif include_profit == best_profit:
            # Tie-breaking: choose lexicographically smaller sequence of original indices
            if include_selected < best_selected:
                best_selected = include_selected
        
        dp[i] = best_profit
        selected[i] = best_selected
    
    return dp[n-1], selected[n-1]

def main():
    """Main function to read input and output results."""
    # Read all input
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    # First token is number of jobs
    n = int(data[0])
    jobs = []
    idx = 1
    
    for _ in range(n):
        start = int(data[idx])
        finish = int(data[idx + 1])
        profit = int(data[idx + 2])
        jobs.append((start, finish, profit))
        idx += 3
    
    # Solve
    max_profit, selected_indices = solve_weighted_interval_scheduling(jobs)
    
    # Output
    print(max_profit)
    print(' '.join(map(str, selected_indices)))

if __name__ == "__main__":
    main()