import heapq

def simulate_priority_queue(jobs):
    """
    Simulates a non-preemptive single-server priority queue with max-priority scheduling.
    
    Tie-breaking hierarchy:
      1. Higher Priority (larger integer value)
      2. Earlier Arrival Time (smaller integer value)
      3. Smaller Job ID (smaller integer value)
      
    Complexity: O(N log N) time, O(N) space.
    """
    if not jobs:
        return [], 0.0

    # Step 1: Sort arrivals by arrival time ascending, then job_id ascending
    sorted_jobs = sorted(jobs, key=lambda x: (x[1], x[0]))
    
    ready_heap = []
    results = []
    
    current_time = 0
    job_idx = 0
    num_jobs = len(sorted_jobs)
    
    while job_idx < num_jobs or ready_heap:
        # Push all jobs that have arrived by current_time
        while job_idx < num_jobs and sorted_jobs[job_idx][1] <= current_time:
            job_id, arrival_time, burst_time, priority = sorted_jobs[job_idx]
            # Priority Heap key formulation for Python's min-heap:
            # (-priority, arrival_time, job_id) ensures max priority, then min arrival, then min job_id
            heapq.heappush(ready_heap, (-priority, arrival_time, job_id, burst_time))
            job_idx += 1
            
        # Handle server idling if heap is empty
        if not ready_heap:
            current_time = sorted_jobs[job_idx][1]
            continue
            
        # Extract next job to execute
        neg_priority, arrival_time, job_id, burst_time = heapq.heappop(ready_heap)
        
        # Calculate timeline metrics
        start_time = max(current_time, arrival_time)
        completion_time = start_time + burst_time
        waiting_time = start_time - arrival_time
        
        results.append((job_id, completion_time, waiting_time))
        current_time = completion_time

    # Sort final per-job output by job_id
    results.sort(key=lambda x: x[0])
    
    total_waiting_time = sum(w for _, _, w in results)
    avg_waiting_time = total_waiting_time / num_jobs if num_jobs > 0 else 0.0
    
    return results, avg_waiting_time


# =====================================================================
# Test Suite
# =====================================================================

def run_tests():
    print("Running Test Suite...\n" + "=" * 50)
    
    # Test 1: Complete Tie-Breaking Test (Priority, Arrival, Job ID)
    # All arrive at t=0, equal priorities -> should execute in order of job_id (1, 2, 3)
    test_1_jobs = [
        (3, 0, 5, 10),
        (1, 0, 2, 10),
        (2, 0, 4, 10),
    ]
    res1, avg1 = simulate_priority_queue(test_1_jobs)
    print("Test 1 - Tie Breaking by Job ID:")
    for r in res1:
        print(f"  Job {r[0]}: Completion={r[1]}, Wait={r[2]}")
    print(f"  Average Waiting Time: {avg1:.2f}\n")
    assert [r[0] for r in sorted(res1, key=lambda x: x[1] - test_1_jobs[x[0]-1][2])] == [1, 2, 3]

    # Test 2: Worst-Case Heap Size & Execution Sequence (Mass Simultaneous Arrival)
    # 1000 jobs arriving at t=0 to force max-depth heap operations O(N log N)
    N = 1000
    test_2_jobs = [(i, 0, 1, i) for i in range(1, N + 1)] # Priority = job_id
    res2, avg2 = simulate_priority_queue(test_2_jobs)
    print(f"Test 2 - Worst-Case Heap Stress ({N} Simultaneous Jobs):")
    # Highest priority (Job 1000) should run first (wait=0), lowest priority (Job 1) should run last (wait=999)
    job_1000_res = next(r for r in res2 if r[0] == 1000)
    job_1_res = next(r for r in res2 if r[0] == 1)
    print(f"  Job 1000 (Max Priority) -> Wait Time: {job_1000_res[2]}")
    print(f"  Job 1    (Min Priority) -> Wait Time: {job_1_res[2]}")
    print(f"  Average Waiting Time: {avg2:.2f}\n")
    assert job_1000_res[2] == 0
    assert job_1_res[2] == N - 1

    # Test 3: Intermittent Server Idle Gaps & Non-Preemption
    # Job 1 starts at t=0 with burst 10. Job 2 (high priority) arrives at t=2.
    # Non-preemption forces Job 2 to wait until Job 1 finishes at t=10.
    test_3_jobs = [
        (1, 0, 10, 1),  # Runs t=0..10
        (2, 2, 3, 100), # Arrives t=2, must wait until t=10
        (3, 20, 5, 5)   # Arrives t=20 after idle gap t=13..20
    ]
    res3, avg3 = simulate_priority_queue(test_3_jobs)
    print("Test 3 - Non-preemption and Idle Time Jump:")
    for r in res3:
        print(f"  Job {r[0]}: Completion={r[1]}, Wait={r[2]}")
    print(f"  Average Waiting Time: {avg3:.2f}\n")
    
    assert next(r for r in res3 if r[0] == 2)[2] == 8  # Wait time: 10 - 2 = 8
    assert next(r for r in res3 if r[0] == 3)[1] == 25 # Completion time: 20 + 5 = 25

    print("=" * 50 + "\nAll tests passed successfully!")

if __name__ == "__main__":
    run_tests()