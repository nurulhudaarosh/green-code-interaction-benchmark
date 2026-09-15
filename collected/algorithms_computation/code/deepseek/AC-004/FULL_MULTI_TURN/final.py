import bisect
from typing import List, Tuple, Union

def job_scheduling(jobs: List[Tuple[int, int, int]]) -> Tuple[int, List[int]]:
    """
    Solve weighted job scheduling problem.
    
    Args:
        jobs: List of (start, finish, profit) tuples
        
    Returns:
        Tuple of (max_profit, list_of_selected_original_indices)
        
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    if not jobs:
        return 0, []
    
    # Add original indices
    indexed_jobs = [(start, finish, profit, idx) for idx, (start, finish, profit) in enumerate(jobs)]
    
    # Sort by finish time (primary), then by start time (secondary) for determinism
    indexed_jobs.sort(key=lambda x: (x[1], x[0]))
    
    n = len(indexed_jobs)
    finish_times = [job[1] for job in indexed_jobs]
    
    # DP arrays: dp_profit[i] = max profit using first i jobs
    # dp_indices[i] = corresponding list of original indices (sorted)
    dp_profit = [0] * (n + 1)
    dp_indices = [[] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        start, finish, profit, orig_idx = indexed_jobs[i-1]
        
        # Find the latest compatible job: finish <= start
        j = bisect.bisect_right(finish_times, start, 0, i-1)
        
        # Option 1: Take this job
        take_profit = profit + dp_profit[j]
        take_indices = dp_indices[j] + [orig_idx]
        take_indices.sort()  # Ensure sorted order for tie-breaking
        
        # Option 2: Skip this job
        skip_profit = dp_profit[i-1]
        skip_indices = dp_indices[i-1]
        
        # Choose the better option
        if take_profit > skip_profit:
            dp_profit[i] = take_profit
            dp_indices[i] = take_indices
        elif skip_profit > take_profit:
            dp_profit[i] = skip_profit
            dp_indices[i] = skip_indices
        else:
            # Tie: choose lexicographically smaller sequence
            if take_indices < skip_indices:
                dp_profit[i] = take_profit
                dp_indices[i] = take_indices
            else:
                dp_profit[i] = skip_profit
                dp_indices[i] = skip_indices
    
    return dp_profit[n], dp_indices[n]


def test_weighted_job_scheduling():
    """Test the implementation with various cases including edge cases."""
    
    print("=" * 60)
    print("TESTING WEIGHTED JOB SCHEDULING")
    print("=" * 60)
    
    # Test 1: Basic case with no overlap
    print("\nTest 1: Basic non-overlapping jobs")
    jobs1 = [(1, 2, 10), (2, 3, 20), (3, 4, 30)]
    profit1, indices1 = job_scheduling(jobs1)
    print(f"Jobs: {jobs1}")
    print(f"Result: profit={profit1}, indices={indices1}")
    assert profit1 == 60, f"Expected 60, got {profit1}"
    assert indices1 == [0, 1, 2], f"Expected [0,1,2], got {indices1}"
    
    # Test 2: Overlapping jobs
    print("\nTest 2: Overlapping jobs")
    jobs2 = [(1, 4, 50), (2, 5, 40), (4, 6, 30)]
    profit2, indices2 = job_scheduling(jobs2)
    print(f"Jobs: {jobs2}")
    print(f"Result: profit={profit2}, indices={indices2}")
    # Option: job0 (50) or job1+job2 (70) but job1 ends at 5, job2 starts at 4 -> compatible? 
    # job1: (2,5), job2: (4,6) -> overlap (5 > 4), so not compatible
    # job0: (1,4) + job2: (4,6) -> compatible (touching at 4) -> profit 80
    assert profit2 == 80, f"Expected 80, got {profit2}"
    assert indices2 == [0, 2], f"Expected [0,2], got {indices2}"
    
    # Test 3: Tie-breaking case (different subsets, same profit)
    print("\nTest 3: Tie-breaking (same profit, different subsets)")
    jobs3 = [(0, 3, 5), (3, 6, 5), (0, 6, 10)]
    profit3, indices3 = job_scheduling(jobs3)
    print(f"Jobs: {jobs3}")
    print(f"Result: profit={profit3}, indices={indices3}")
    # Option A: jobs 0 and 1 -> profit 10, indices [0,1]
    # Option B: job 2 -> profit 10, indices [2]
    # Lexicographically: [0,1] < [2], so choose [0,1]
    assert profit3 == 10, f"Expected 10, got {profit3}"
    assert indices3 == [0, 1], f"Expected [0,1], got {indices3}"
    
    # Test 4: Multiple tie-breakings with unsorted original indices
    print("\nTest 4: Complex tie-breaking with unsorted original indices")
    jobs4 = [(0, 10, 10), (2, 4, 5), (4, 6, 5)]
    profit4, indices4 = job_scheduling(jobs4)
    print(f"Jobs: {jobs4}")
    print(f"Result: profit={profit4}, indices={indices4}")
    # Option A: job0 (profit 10, indices [0])
    # Option B: job1+job2 (profit 10, indices [1,2])
    # Lexicographically: [0] < [1,2], so choose [0]
    assert profit4 == 10, f"Expected 10, got {profit4}"
    assert indices4 == [0], f"Expected [0], got {indices4}"
    
    # Test 5: Empty input
    print("\nTest 5: Empty input")
    jobs5 = []
    profit5, indices5 = job_scheduling(jobs5)
    print(f"Jobs: {jobs5}")
    print(f"Result: profit={profit5}, indices={indices5}")
    assert profit5 == 0, f"Expected 0, got {profit5}"
    assert indices5 == [], f"Expected [], got {indices5}"
    
    # Test 6: Single job
    print("\nTest 6: Single job")
    jobs6 = [(5, 10, 100)]
    profit6, indices6 = job_scheduling(jobs6)
    print(f"Jobs: {jobs6}")
    print(f"Result: profit={profit6}, indices={indices6}")
    assert profit6 == 100, f"Expected 100, got {profit6}"
    assert indices6 == [0], f"Expected [0], got {indices6}"
    
    # Test 7: All jobs overlap
    print("\nTest 7: All jobs overlap")
    jobs7 = [(1, 5, 10), (2, 4, 20), (3, 6, 15)]
    profit7, indices7 = job_scheduling(jobs7)
    print(f"Jobs: {jobs7}")
    print(f"Result: profit={profit7}, indices={indices7}")
    # Best is max single job: job1 (profit 20)
    assert profit7 == 20, f"Expected 20, got {profit7}"
    assert indices7 == [1], f"Expected [1], got {indices7}"
    
    # Test 8: Jobs with zero profit
    print("\nTest 8: Jobs with zero profit")
    jobs8 = [(0, 5, 0), (5, 10, 0), (2, 7, 0)]
    profit8, indices8 = job_scheduling(jobs8)
    print(f"Jobs: {jobs8}")
    print(f"Result: profit={profit8}, indices={indices8}")
    # Max profit is 0, choose lexicographically smallest non-empty set? 
    # Actually, with all profits 0, best is empty set (profit 0)
    # But the problem likely expects the maximum number of jobs? No, the requirement is max profit.
    # With profit 0, any subset works. The tie-breaking should choose lexicographically smallest sequence.
    # The empty set [] is lexicographically smallest.
    assert profit8 == 0, f"Expected 0, got {profit8}"
    assert indices8 == [], f"Expected [], got {indices8}"
    
    # Test 9: Large number of jobs (stress test for O(n log n))
    print("\nTest 9: Stress test with 1000 jobs")
    import random
    random.seed(42)  # Deterministic
    n = 1000
    jobs9 = []
    for i in range(n):
        start = random.randint(0, 1000)
        finish = start + random.randint(1, 100)
        profit = random.randint(1, 100)
        jobs9.append((start, finish, profit))
    
    profit9, indices9 = job_scheduling(jobs9)
    print(f"Processed {n} jobs")
    print(f"Max profit: {profit9}")
    print(f"Number of selected jobs: {len(indices9)}")
    # Verify selected jobs are non-overlapping
    selected = [(jobs9[idx][0], jobs9[idx][1], idx) for idx in indices9]
    selected.sort(key=lambda x: x[1])
    for i in range(len(selected)-1):
        assert selected[i][1] <= selected[i+1][0], f"Overlap detected: {selected[i]} and {selected[i+1]}"
    print("✓ All selected jobs are non-overlapping")
    
    # Test 10: Touching endpoints compatibility
    print("\nTest 10: Touching endpoints (should be compatible)")
    jobs10 = [(0, 5, 10), (5, 10, 20), (10, 15, 30)]
    profit10, indices10 = job_scheduling(jobs10)
    print(f"Jobs: {jobs10}")
    print(f"Result: profit={profit10}, indices={indices10}")
    # All touch at endpoints, should all be selected
    assert profit10 == 60, f"Expected 60, got {profit10}"
    assert indices10 == [0, 1, 2], f"Expected [0,1,2], got {indices10}"
    
    # Test 11: Worst-case-like structure (many jobs with same finish time)
    print("\nTest 11: Worst-case structure (many jobs with same finish time)")
    jobs11 = [(i, 100, i+1) for i in range(50)]  # All end at 100, different starts
    profit11, indices11 = job_scheduling(jobs11)
    print(f"50 jobs all ending at 100")
    print(f"Result: profit={profit11}, indices={indices11}")
    # Only one job can be chosen (since all overlap). Choose the one with highest profit.
    # Highest profit is at index 49 (profit 50)
    assert profit11 == 50, f"Expected 50, got {profit11}"
    assert indices11 == [49], f"Expected [49], got {indices11}"
    
    # Test 12: Worst-case-like structure (many jobs with same start time)
    print("\nTest 12: Worst-case structure (many jobs with same start time)")
    jobs12 = [(0, i+1, i+1) for i in range(50)]  # All start at 0
    profit12, indices12 = job_scheduling(jobs12)
    print(f"50 jobs all starting at 0")
    print(f"Result: profit={profit12}, indices={indices12}")
    # Again only one job can be chosen. Choose highest profit (index 49, profit 50)
    assert profit12 == 50, f"Expected 50, got {profit12}"
    assert indices12 == [49], f"Expected [49], got {indices12}"
    
    # Test 13: Binary search edge case (exact match with finish == start)
    print("\nTest 13: Edge case (finish == start)")
    jobs13 = [(0, 5, 10), (5, 10, 20), (5, 15, 15)]
    profit13, indices13 = job_scheduling(jobs13)
    print(f"Jobs: {jobs13}")
    print(f"Result: profit={profit13}, indices={indices13}")
    # job0 + job1 = 30, job0 + job2 = 25, job1 alone = 20
    # Best: job0 + job1 = 30
    assert profit13 == 30, f"Expected 30, got {profit13}"
    assert indices13 == [0, 1], f"Expected [0,1], got {indices13}"
    
    # Test 14: Negative or zero duration (invalid, but handle gracefully)
    print("\nTest 14: Zero-duration jobs")
    jobs14 = [(5, 5, 10), (5, 5, 20), (4, 6, 15)]
    profit14, indices14 = job_scheduling(jobs14)
    print(f"Jobs: {jobs14}")
    print(f"Result: profit={profit14}, indices={indices14}")
    # zero-duration jobs are compatible with each other if they start at same time
    # job1 (profit 20) + anything else? job1 and job2: (5,5) and (4,6) overlap (5>4, no)
    # Best is max single: job1 (profit 20) or job2 (profit 15)
    assert profit14 == 20, f"Expected 20, got {profit14}"
    assert indices14 == [1], f"Expected [1], got {indices14}"
    
    # Test 15: Complex tie with three equal options
    print("\nTest 15: Three-way tie")
    jobs15 = [
        (0, 5, 10),   # index 0
        (5, 10, 10),  # index 1
        (0, 10, 20),  # index 2
        (10, 15, 5),  # index 3
    ]
    profit15, indices15 = job_scheduling(jobs15)
    print(f"Jobs: {jobs15}")
    print(f"Result: profit={profit15}, indices={indices15}")
    # Options:
    # - [0,1,3] = 10+10+5 = 25
    # - [2,3] = 20+5 = 25
    # - [0,3] = 15
    # - [1,3] = 15
    # Best: [0,1,3] vs [2,3], lexicographically [0,1,3] < [2,3]
    assert profit15 == 25, f"Expected 25, got {profit15}"
    assert indices15 == [0, 1, 3], f"Expected [0,1,3], got {indices15}"
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_weighted_job_scheduling()