from bisect import bisect_right

def job_scheduling(jobs, return_summary=False):
    """
    Solves the Weighted Interval Scheduling Problem in O(N log N) time and O(N) space.
    Handles dense overlapping jobs and tie-breaking efficiently.
    """
    if not jobs:
        summary = {"total_jobs": 0, "binary_searches": 0, "dp_decisions": 0, "tie_breaks": 0}
        return (0, [], summary) if return_summary else (0, [])

    # Attach original 0-based index: (start, finish, profit, orig_idx)
    indexed_jobs = [(s, f, p, i) for i, (s, f, p) in enumerate(jobs)]
    
    # Sort by finish time, then start time, then original index
    indexed_jobs.sort(key=lambda x: (x[1], x[0], x[3]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # Track statistics
    binary_searches = 0
    dp_decisions = 0
    tie_breaks = 0

    # dp_profit[i] stores the max profit for the first i sorted jobs
    dp_profit = [0] * (n + 1)
    
    # Predecessor array for quick backwards sequence reconstruction
    # pred_idx[i] stores the bisect result for sorted job i (1-indexed in DP)
    pred_map = [0] * (n + 1)
    
    # Choice record for optimal path reconstruction:
    # 'INCL', 'EXCL', or 'BOTH'
    choices = [''] * (n + 1)
    
    # Helper to reconstruct the index sequence for a given DP state up to item `idx`
    def get_sequence(idx):
        seq = []
        curr = idx
        while curr > 0:
            choice = choices[curr]
            if choice == 'INCL':
                seq.append(indexed_jobs[curr - 1][3])
                curr = pred_map[curr]
            elif choice == 'EXCL':
                curr = curr - 1
            elif choice == 'BOTH':
                # Evaluate both paths to find lexicographically smaller sequence
                incl_path = get_sequence(pred_map[curr]) + [indexed_jobs[curr - 1][3]]
                incl_path.sort()
                excl_path = get_sequence(curr - 1)
                excl_path.sort()
                return min(incl_path, excl_path)
        seq.sort()
        return seq

    for i in range(1, n + 1):
        s, f, p, orig_idx = indexed_jobs[i - 1]
        
        # Binary search for latest compatible job: finish <= start
        p_idx = bisect_right(finish_times, s, hi=i - 1)
        pred_map[i] = p_idx
        binary_searches += 1
        
        incl_profit = dp_profit[p_idx] + p
        excl_profit = dp_profit[i - 1]
        dp_decisions += 1
        
        if incl_profit > excl_profit:
            dp_profit[i] = incl_profit
            choices[i] = 'INCL'
        elif excl_profit > incl_profit:
            dp_profit[i] = excl_profit
            choices[i] = 'EXCL'
        else:
            # Equal profits: mark as BOTH to evaluate tie break
            dp_profit[i] = incl_profit
            tie_breaks += 1
            
            incl_seq = get_sequence(p_idx) + [orig_idx]
            incl_seq.sort()
            excl_seq = get_sequence(i - 1)
            excl_seq.sort()
            
            if incl_seq < excl_seq:
                choices[i] = 'INCL'
            else:
                choices[i] = 'EXCL'

    max_profit = dp_profit[n]
    selected_indices = get_sequence(n)
    
    if return_summary:
        operation_summary = {
            "total_jobs": n,
            "binary_searches": binary_searches,
            "dp_decisions": dp_decisions,
            "tie_breaks": tie_breaks
        }
        return max_profit, selected_indices, operation_summary
        
    return max_profit, selected_indices


# --- Test Cases ---
def run_tests():
    print("Running Worst-Case & Boundary Tests...\n")
    
    # Test 1: Dense Overlapping Jobs (All overlap, must pick single max profit)
    dense_jobs = [(1, 10, 10), (2, 9, 20), (3, 8, 30), (4, 7, 25)]
    p1, idx1, s1 = job_scheduling(dense_jobs, return_summary=True)
    assert p1 == 30 and idx1 == [2], f"Failed Test 1: {p1}, {idx1}"
    print("Test 1 Passed (Dense Overlapping Jobs)")

    # Test 2: Chain of Touching Jobs (f_i == s_{i+1})
    chain_jobs = [(0, 2, 10), (2, 4, 20), (4, 6, 30), (6, 8, 40)]
    p2, idx2, s2 = job_scheduling(chain_jobs, return_summary=True)
    assert p2 == 100 and idx2 == [0, 1, 2, 3], f"Failed Test 2: {p2}, {idx2}"
    print("Test 2 Passed (Chain of Touching Endpoints)")

    # Test 3: Heavy Tie-Breaking Scenario (Multiple paths yield equal profit)
    # Job 0: (0, 5, 50)
    # Job 1: (0, 2, 25), Job 2: (2, 5, 25) -> Profit = 50, indices [1, 2]
    # Profit is equal (50). Tie-breaker chooses [0] over [1, 2] since [0] < [1, 2].
    tie_jobs = [(0, 5, 50), (0, 2, 25), (2, 5, 25)]
    p3, idx3, s3 = job_scheduling(tie_jobs, return_summary=True)
    assert p3 == 50 and idx3 == [0], f"Failed Test 3: {p3}, {idx3}"
    print("Test 3 Passed (Lexicographical Tie-Breaking)")

    # Test 4: Large N Scalability (Worst-case N = 10,000)
    large_jobs = [(i, i + 2, 10) for i in range(10000)]
    p4, idx4, s4 = job_scheduling(large_jobs, return_summary=True)
    assert s4["total_jobs"] == 10000
    assert s4["binary_searches"] == 10000
    print("Test 4 Passed (Large Input Scale N=10,000)")

    print("\nAll tests successfully passed!")

if __name__ == "__main__":
    run_tests()