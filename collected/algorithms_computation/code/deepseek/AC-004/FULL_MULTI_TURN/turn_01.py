import bisect

def job_scheduling(jobs):
    """
    jobs: list of tuples (start, finish, profit)
    Returns: (max_profit, list_of_indices_in_original_order)
    """
    # add original index to each job
    indexed_jobs = [(start, finish, profit, idx) for idx, (start, finish, profit) in enumerate(jobs)]
    # sort by finish time
    indexed_jobs.sort(key=lambda x: x[1])
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # dp_profit[i] = max profit using first i jobs (i from 0 to n)
    dp_profit = [0] * (n + 1)
    # dp_indices[i] = list of original indices for that max profit
    dp_indices = [[] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i-1]
        
        # find the latest job with finish <= start
        j = bisect.bisect_right(finish_times, start, 0, i-1)  # among first i-1 jobs (0-indexed)
        # j is the count of jobs with finish <= start, so predecessor index = j (since dp uses 1-indexed)
        
        # option: take this job
        take_profit = profit + dp_profit[j]
        take_indices = dp_indices[j] + [orig_idx]
        
        # option: skip this job
        skip_profit = dp_profit[i-1]
        skip_indices = dp_indices[i-1]
        
        # choose better: higher profit; if tie, lexicographically smaller indices
        if take_profit > skip_profit:
            dp_profit[i] = take_profit
            dp_indices[i] = take_indices
        elif skip_profit > take_profit:
            dp_profit[i] = skip_profit
            dp_indices[i] = skip_indices
        else:
            # tie: choose lexicographically smaller list
            if take_indices < skip_indices:
                dp_profit[i] = take_profit
                dp_indices[i] = take_indices
            else:
                dp_profit[i] = skip_profit
                dp_indices[i] = skip_indices
    
    return dp_profit[n], dp_indices[n]

# Example usage (only for self-test, not required for final output)
if __name__ == "__main__":
    # Example: jobs = [(1,3,5), (2,5,6), (4,6,5), (6,7,4)]
    # The optimal is job 0 + job 2 + job 3 (indices 0,2,3) profit 14, or job 1+job3 profit 10, etc.
    jobs = [(1,3,5), (2,5,6), (4,6,5), (6,7,4)]
    profit, indices = job_scheduling(jobs)
    print("Max profit:", profit)
    print("Indices:", indices)