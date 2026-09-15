import bisect

def job_scheduling(jobs):
    """
    jobs: list of tuples (start, finish, profit)
    Returns: (max_profit, list_of_indices_in_original_order, operation_summary)
    """
    # Add original index to each job
    indexed_jobs = [(start, finish, profit, idx) for idx, (start, finish, profit) in enumerate(jobs)]
    # Sort by finish time
    indexed_jobs.sort(key=lambda x: x[1])
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # DP arrays
    dp_profit = [0] * (n + 1)
    dp_indices = [[] for _ in range(n + 1)]
    
    # Operation counters
    comparisons = 0
    binary_searches = 0
    
    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i-1]
        
        # Find latest compatible predecessor
        j = bisect.bisect_right(finish_times, start, 0, i-1)
        binary_searches += 1
        
        # Option: take this job
        take_profit = profit + dp_profit[j]
        take_indices = dp_indices[j] + [orig_idx]
        # Sort the indices to maintain increasing order
        take_indices.sort()
        
        # Option: skip this job
        skip_profit = dp_profit[i-1]
        skip_indices = dp_indices[i-1]
        
        comparisons += 1
        
        # Choose better: higher profit; if tie, lexicographically smaller indices
        if take_profit > skip_profit:
            dp_profit[i] = take_profit
            dp_indices[i] = take_indices
        elif skip_profit > take_profit:
            dp_profit[i] = skip_profit
            dp_indices[i] = skip_indices
        else:
            # Tie: choose lexicographically smaller list
            if take_indices < skip_indices:
                dp_profit[i] = take_profit
                dp_indices[i] = take_indices
            else:
                dp_profit[i] = skip_profit
                dp_indices[i] = skip_indices
    
    operation_summary = {
        'total_comparisons': comparisons,
        'total_binary_searches': binary_searches,
        'total_operations': comparisons + binary_searches
    }
    
    return dp_profit[n], dp_indices[n], operation_summary


# Demonstration with a small example
if __name__ == "__main__":
    # Example where tie-breaking matters
    jobs = [
        (0, 3, 5),   # index 0
        (3, 6, 5),   # index 1 (touching, compatible with 0)
        (0, 6, 10),  # index 2 (covers both)
    ]
    
    profit, indices, summary = job_scheduling(jobs)
    print("Max profit:", profit)
    print("Selected indices:", indices)
    print("Operation summary:", summary)
    
    # Another example
    jobs2 = [
        (1, 4, 10),  # index 0
        (2, 3, 5),   # index 1
        (3, 5, 10),  # index 2
    ]
    
    profit2, indices2, summary2 = job_scheduling(jobs2)
    print("\nMax profit:", profit2)
    print("Selected indices:", indices2)
    print("Operation summary:", summary2)