import heapq

def simulate_priority_queue(jobs, include_summary=False):
    """
    Simulates a non-preemptive single-server priority queue with deterministic tie-breaking.
    
    Tie-breaking order:
      1. Higher priority (larger numerical value)
      2. Earlier arrival time
      3. Smaller job ID
    """
    if not jobs:
        empty_summary = {
            'total_jobs_processed': 0,
            'total_enqueues': 0,
            'total_dequeues': 0,
            'total_clock_jumps': 0,
            'total_major_operations': 0
        }
        return ({}, 0.0, empty_summary) if include_summary else ({}, 0.0)

    # Sort initial arrivals by arrival time, then by job ID for deterministic processing
    sorted_jobs = sorted(jobs, key=lambda x: (x['arrival'], x['id']))
    
    n = len(sorted_jobs)
    job_idx = 0
    current_time = 0
    
    ready_queue = []  # Heap storing: (-priority, arrival, job_id, duration)
    results = {}
    total_waiting_time = 0

    # Operational metrics counters
    num_enqueues = 0
    num_dequeues = 0
    num_clock_jumps = 0

    while job_idx < n or ready_queue:
        # Step 1: Jump current_time forward if server is idle and no jobs are ready
        if not ready_queue and current_time < sorted_jobs[job_idx]['arrival']:
            current_time = sorted_jobs[job_idx]['arrival']
            num_clock_jumps += 1
        
        # Step 2: Enqueue ALL jobs that have arrived up to current_time BEFORE popping
        while job_idx < n and sorted_jobs[job_idx]['arrival'] <= current_time:
            job = sorted_jobs[job_idx]
            heapq.heappush(
                ready_queue, 
                (-job['priority'], job['arrival'], job['id'], job['duration'])
            )
            job_idx += 1
            num_enqueues += 1

        # Step 3: Process the highest-priority available job
        neg_prio, arrival, job_id, duration = heapq.heappop(ready_queue)
        num_dequeues += 1
        
        start_time = current_time
        waiting_time = start_time - arrival
        completion_time = start_time + duration
        current_time = completion_time
        
        total_waiting_time += waiting_time
        results[job_id] = {
            'completion_time': completion_time,
            'waiting_time': waiting_time
        }

    avg_waiting_time = total_waiting_time / n if n > 0 else 0.0

    if include_summary:
        operation_summary = {
            'total_jobs_processed': n,
            'total_enqueues': num_enqueues,
            'total_dequeues': num_dequeues,
            'total_clock_jumps': num_clock_jumps,
            'total_major_operations': num_enqueues + num_dequeues + num_clock_jumps
        }
        return results, avg_waiting_time, operation_summary

    return results, avg_waiting_time


# ==========================================
# Test Suite for Edge Cases & Worst-Case Inputs
# ==========================================

def run_tests():
    # Test 1: Max Heap Contention (Worst-Case Heap Size & Reverse Priority Order)
    # Job 1 locks server from t=0 to t=100. Jobs 2..5 arrive during Job 1.
    # Higher ID/arrival jobs have higher priority, testing reverse-order heap extraction.
    worst_case_jobs = [
        {'id': 1, 'arrival': 0, 'duration': 100, 'priority': 1},
        {'id': 2, 'arrival': 1, 'duration': 10,  'priority': 2},
        {'id': 3, 'arrival': 2, 'duration': 10,  'priority': 3},
        {'id': 4, 'arrival': 3, 'duration': 10,  'priority': 4},
        {'id': 5, 'arrival': 4, 'duration': 10,  'priority': 5},
    ]
    res, avg_w, summary = simulate_priority_queue(worst_case_jobs, include_summary=True)
    assert res[1]['completion_time'] == 100 and res[1]['waiting_time'] == 0
    assert res[5]['completion_time'] == 110 and res[5]['waiting_time'] == 106  # Highest priority after job 1
    assert res[4]['completion_time'] == 120 and res[4]['waiting_time'] == 117
    assert summary['total_enqueues'] == 5 and summary['total_dequeues'] == 5

    # Test 2: Identical Priority and Simultaneous Arrivals (Tie-Breaker Test)
    # Jobs 1, 2, 3 arrive at t=0 with identical priority=5. Must break ties by Job ID.
    tie_jobs = [
        {'id': 3, 'arrival': 0, 'duration': 5, 'priority': 5},
        {'id': 1, 'arrival': 0, 'duration': 5, 'priority': 5},
        {'id': 2, 'arrival': 0, 'duration': 5, 'priority': 5},
    ]
    res, avg_w = simulate_priority_queue(tie_jobs)
    assert res[1]['completion_time'] == 5   and res[1]['waiting_time'] == 0
    assert res[2]['completion_time'] == 10  and res[2]['waiting_time'] == 5
    assert res[3]['completion_time'] == 15  and res[3]['waiting_time'] == 10

    # Test 3: Multiple Idle Clock Jumps
    # Sparse job arrivals with gaps forces multiple clock jumps.
    sparse_jobs = [
        {'id': 1, 'arrival': 0,   'duration': 5, 'priority': 1},
        {'id': 2, 'arrival': 100, 'duration': 5, 'priority': 1},
        {'id': 3, 'arrival': 200, 'duration': 5, 'priority': 1},
    ]
    res, avg_w, summary = simulate_priority_queue(sparse_jobs, include_summary=True)
    assert res[1]['completion_time'] == 5   and res[1]['waiting_time'] == 0
    assert res[2]['completion_time'] == 105 and res[2]['waiting_time'] == 0
    assert res[3]['completion_time'] == 205 and res[3]['waiting_time'] == 0
    assert summary['total_clock_jumps'] == 3

    # Test 4: Empty Input
    res, avg_w, summary = simulate_priority_queue([], include_summary=True)
    assert res == {} and avg_w == 0.0 and summary['total_jobs_processed'] == 0

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()