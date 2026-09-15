from bisect import bisect_right
from typing import List, Tuple, Dict, Any

def max_profit_weighted_interval_scheduling(jobs: List[Dict[str, int]]) -> Tuple[int, List[int]]:
    """
    Solves the Weighted Interval Scheduling problem with deterministic tie-breaking.
    
    :param jobs: List of dicts, each with 'start', 'finish', and 'profit'.
    :return: Tuple containing (max_profit, list_of_selected_original_indices)
    """
    if not jobs:
        return 0, []

    # Attach original index to each job
    indexed_jobs = []
    for orig_idx, job in enumerate(jobs):
        indexed_jobs.append({
            'start': job['start'],
            'finish': job['finish'],
            'profit': job['profit'],
            'orig_idx': orig_idx
        })

    # Sort primarily by finish time, secondarily by start time and original index
    indexed_jobs.sort(key=lambda j: (j['finish'], j['start'], j['orig_idx']))
    
    n = len(indexed_jobs)
    finish_times = [j['finish'] for j in indexed_jobs]

    # dp[i] = (max_profit, selected_orig_indices_list) for considering first i sorted jobs
    dp: List[Tuple[int, List[int]]] = [(0, [])] * (n + 1)

    for i in range(1, n + 1):
        current_job = indexed_jobs[i - 1]
        
        # Binary search for the latest job that finishes <= current_job['start']
        # bisect_right returns index in finish_times where current_job['start'] can be inserted
        pred_idx = bisect_right(finish_times, current_job['start'])

        # Option 1: Exclude the current job
        profit_exclude, seq_exclude = dp[i - 1]

        # Option 2: Include the current job
        profit_pred, seq_pred = dp[pred_idx]
        profit_include = profit_pred + current_job['profit']
        
        # Maintain sorted order of original indices for deterministic comparison
        seq_include = sorted(seq_pred + [current_job['orig_idx']])

        # Compare options: Maximize profit, break ties with lexicographically smaller index list
        if profit_include > profit_exclude:
            dp[i] = (profit_include, seq_include)
        elif profit_exclude > profit_include:
            dp[i] = (profit_exclude, seq_exclude)
        else:
            # Profits are equal -> pick lexicographically smaller original index sequence
            if seq_include < seq_exclude:
                dp[i] = (profit_include, seq_include)
            else:
                dp[i] = (profit_exclude, seq_exclude)

    return dp[n]


# Example Usage
if __name__ == "__main__":
    job_list = [
        {"start": 1, "finish": 3, "profit": 50},  # Index 0
        {"start": 2, "finish": 5, "profit": 20},  # Index 1
        {"start": 3, "finish": 6, "profit": 100}, # Index 2
        {"start": 6, "finish": 9, "profit": 60}   # Index 3
    ]

    max_profit, selected_indices = max_profit_weighted_interval_scheduling(job_list)
    print(f"Maximum Profit: {max_profit}")
    print(f"Selected Job Indices: {selected_indices}")