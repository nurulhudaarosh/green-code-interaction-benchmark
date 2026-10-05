import heapq

def simulate_queue(jobs):
    """
    Simulates a non-preemptive single-server queue with deterministic tie handling.
    
    Tie-breaking order:
      1. Larger priority (-priority for min-heap)
      2. Earlier arrival time
      3. Smaller job ID
      
    Input tuple format: (job_id, arrival_time, duration, priority)
    """
    # Sort initial jobs by arrival time, then priority (desc), then job_id (asc)
    sorted_jobs = sorted(jobs, key=lambda x: (x[1], -x[3], x[0]))
    
    ready_heap = []
    results = {}
    current_time = 0
    job_idx = 0
    num_jobs = len(sorted_jobs)
    
    while job_idx < num_jobs or ready_heap:
        # 1. Advance time to the next arrival if server is idle and heap is empty
        if not ready_heap and current_time < sorted_jobs[job_idx][1]:
            current_time = sorted_jobs[job_idx][1]
            
        # 2. Push ALL jobs that have arrived on or before current_time into ready_heap
        while job_idx < num_jobs and sorted_jobs[job_idx][1] <= current_time:
            j_id, arr_time, dur, prio = sorted_jobs[job_idx]
            # Priority Heap Key: (-priority, arrival_time, job_id, duration)
            heapq.heappush(ready_heap, (-prio, arr_time, j_id, dur))
            job_idx += 1
            
        # 3. Pop highest-priority ready job (guaranteed correct tie handling via tuple sorting)
        neg_prio, arr_time, j_id, dur = heapq.heappop(ready_heap)
        
        start_time = current_time
        wait_time = start_time - arr_time
        completion_time = start_time + dur
        current_time = completion_time
        
        results[j_id] = {
            "job_id": j_id,
            "completion_time": completion_time,
            "waiting_time": wait_time
        }
    
    # Format output in original input order
    ordered_results = [results[j[0]] for j in jobs]
    total_wait_time = sum(res["waiting_time"] for res in ordered_results)
    avg_wait_time = total_wait_time / num_jobs if num_jobs > 0 else 0.0
    
    return ordered_results, avg_wait_time


if __name__ == "__main__":
    # Test case with simultaneous arrival tie-break:
    # Both Job 2 and Job 1 arrive at time 5 with equal priority 10.
    # Job 1 must run first because Job ID 1 < Job ID 2.
    test_jobs = [
        (2, 5, 3, 10),
        (1, 5, 2, 10)
    ]
    
    metrics, avg_wait = simulate_queue(test_jobs)
    
    print("Execution Order & Metrics:")
    for m in metrics:
        print(f"Job {m['job_id']}: Completion = {m['completion_time']}, Waiting = {m['waiting_time']}")
    print(f"Average Waiting Time: {avg_wait:.2f}")