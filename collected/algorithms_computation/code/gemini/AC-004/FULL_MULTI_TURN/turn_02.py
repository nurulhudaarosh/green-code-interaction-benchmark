from bisect import bisect_right

def job_scheduling(jobs):
    """
    Solves the Weighted Interval Scheduling Problem with exact deterministic tie-breaking.
    
    Parameters:
    jobs (list of tuples/lists): Each element is (start, finish, profit)
    
    Returns:
    tuple: (max_profit, list_of_selected_original_indices)
    """
    if not jobs:
        return 0, []

    n = len(jobs)
    
    # Preserve original indices: (start, finish, profit, original_index)
    indexed_jobs = [(s, f, p, i) for i, (s, f, p) in enumerate(jobs)]
    
    # Sort primarily by finish time, then start time, then original index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    finish_times = [job[1] for job in indexed_jobs]
    
    # Find predecessor index for each job in sorted array
    preds = []
    for i in range(n):
        s = indexed_jobs[i][0]
        p_idx = bisect_right(finish_times, s, hi=i) - 1
        preds.append(p_idx)

    # dp[i] = max profit considering a subset of the first i sorted jobs
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        s, f, p, orig_idx = indexed_jobs[i - 1]
        pred_idx = preds[i - 1]
        
        incl_profit = (dp[pred_idx + 1] if pred_idx != -1 else 0) + p
        excl_profit = dp[i - 1]
        
        dp[i] = max(incl_profit, excl_profit)

    max_profit = dp[n]

    # Memoized backtracking to reconstruct the lexicographically smallest sequence of original indices
    memo = {}

    def get_best_sequence(i):
        """Returns the lexicographically smallest index list that achieves 
        the maximum possible profit for the prefix up to sorted job i."""
        if i == 0:
            return []
        if i in memo:
            return memo[i]

        s, f, p, orig_idx = indexed_jobs[i - 1]
        pred_idx = preds[i - 1]
        
        incl_profit = (dp[pred_idx + 1] if pred_idx != -1 else 0) + p
        excl_profit = dp[i - 1]
        
        candidates = []
        
        # Option 1: Exclude job i (if it achieves the optimal profit for dp[i])
        if excl_profit == dp[i]:
            candidates.append(get_best_sequence(i - 1))
            
        # Option 2: Include job i (if it achieves the optimal profit for dp[i])
        if incl_profit == dp[i]:
            prev_seq = get_best_sequence(pred_idx + 1) if pred_idx != -1 else []
            candidates.append(sorted(prev_seq + [orig_idx]))

        # Pick the lexicographically smallest list among valid optimal candidates
        best_seq = min(candidates)
        memo[i] = best_seq
        return best_seq

    best_indices = get_best_sequence(n)
    return max_profit, best_indices


# --- Verification with Counterexample ---
if __name__ == "__main__":
    sample_jobs = [
        (0, 5, 10), # Job 0
        (0, 2, 5),  # Job 1
        (2, 5, 5)   # Job 2
    ]
    
    max_profit, chosen_jobs = job_scheduling(sample_jobs)
    print(f"Maximum Profit: {max_profit}")
    print(f"Selected Original Indices: {chosen_jobs}")
    # Output:
    # Maximum Profit: 10
    # Selected Original Indices: [0]