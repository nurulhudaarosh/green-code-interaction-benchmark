import heapq

def simulate_priority_queue(jobs):
    """
    Simulates a non-preemptive single-server priority queue.
    
    :param jobs: List of dicts or tuples representing jobs.
                 Expected format: [{'id': int/str, 'arrival': float/int, 'burst': float/int, 'priority': int/float}, ...]
    :return: Tuple (job_results, average_waiting_time)
    """
    # Sort incoming jobs by arrival time initially
    sorted_jobs = sorted(jobs, key=lambda j: (j['arrival'], j['id']))
    
    current_time = 0
    ready_heap = []
    results = {}
    job_idx = 0
    total_jobs = len(sorted_jobs)
    processed_count = 0
    
    while processed_count < total_jobs:
        # Push all jobs that have arrived by current_time into the ready queue
        while job_idx < total_jobs and sorted_jobs[job_idx]['arrival'] <= current_time:
            j = sorted_jobs[job_idx]
            # heapq is a min-heap, so negate priority for max-priority ordering
            heapq.heappush(ready_heap, (-j['priority'], j['arrival'], j['id'], j['burst']))
            job_idx += 1
            
        # If no jobs are ready, jump time forward to the next job's arrival time
        if not ready_heap:
            current_time = sorted_jobs[job_idx]['arrival']
            continue
            
        # Select job with highest priority (tie-breakers: earlier arrival, smaller job ID)
        neg_prio, arrival, job_id, burst = heapq.heappop(ready_heap)
        priority = -neg_prio
        
        start_time = current_time
        completion_time = start_time + burst
        waiting_time = start_time - arrival
        
        results[job_id] = {
            'id': job_id,
            'arrival': arrival,
            'burst': burst,
            'priority': priority,
            'start_time': start_time,
            'completion_time': completion_time,
            'waiting_time': waiting_time
        }
        
        current_time = completion_time
        processed_count += 1

    avg_waiting_time = sum(res['waiting_time'] for res in results.values()) / total_jobs if total_jobs > 0 else 0.0
    return results, avg_waiting_time


# Example Usage & Verification
if __name__ == "__main__":
    sample_jobs = [
        {'id': 1, 'arrival': 0, 'burst': 5, 'priority': 2},
        {'id': 2, 'arrival': 1, 'burst': 3, 'priority': 5},
        {'id': 3, 'arrival': 2, 'burst': 4, 'priority': 5},
        {'id': 4, 'arrival': 10, 'burst': 2, 'priority': 1},
    ]

    results, avg_wait = simulate_priority_queue(sample_jobs)
    
    print(f"{'Job ID':<8}{'Arrival':<10}{'Burst':<8}{'Priority':<10}{'Completion':<14}{'Waiting Time':<12}")
    print("-" * 62)
    for job_id in sorted(results.keys()):
        res = results[job_id]
        print(f"{res['id']:<8}{res['arrival']:<10}{res['burst']:<8}{res['priority']:<10}{res['completion_time']:<14}{res['waiting_time']:<12}")
    
    print("-" * 62)
    print(f"Average Waiting Time: {avg_wait:.2f}")