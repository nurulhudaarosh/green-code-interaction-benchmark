import heapq

def simulate_queue(jobs):
    """
    Simulates a non-preemptive priority queue server.
    
    :param jobs: List of tuples/dicts representing jobs:
                 (job_id, arrival_time, duration, priority)
    :return: List of results per job and average waiting time.
    """
    # Sort jobs by arrival time initially
    # Structure: (arrival_time, job_id, duration, priority)
    sorted_jobs = sorted(jobs, key=lambda x: (x[1], x[0]))
    
    n = len(sorted_jobs)
    job_idx = 0
    current_time = 0
    pq = []  # Min-heap storing (-priority, arrival_time, job_id, duration)
    
    results = {}
    
    while job_idx < n or pq:
        # If queue is empty and server is idle, jump time forward to next arrival
        if not pq and current_time < sorted_jobs[job_idx][1]:
            current_time = sorted_jobs[job_idx][1]
            
        # Add all jobs that have arrived by current_time
        while job_idx < n and sorted_jobs[job_idx][1] <= current_time:
            j_id, arr_time, dur, prio = sorted_jobs[job_idx]
            # Negate priority for Max-Heap behavior
            heapq.heappush(pq, (-prio, arr_time, j_id, dur))
            job_idx += 1
            
        # Process the highest priority job
        neg_prio, arr_time, j_id, dur = heapq.heappop(pq)
        prio = -neg_prio
        
        start_time = current_time
        wait_time = start_time - arr_time
        completion_time = start_time + dur
        current_time = completion_time
        
        results[j_id] = {
            "job_id": j_id,
            "completion_time": completion_time,
            "waiting_time": wait_time
        }
        
    # Calculate average waiting time
    total_wait = sum(res["waiting_time"] for res in results.values())
    avg_wait = total_wait / n if n > 0 else 0.0
    
    return results, avg_wait


# --- Example Usage ---
if __name__ == "__main__":
    # Job format: (job_id, arrival_time, duration, priority)
    sample_jobs = [
        (1, 0, 5, 2),  # Job 1 arrives at 0, duration 5, priority 2
        (2, 1, 3, 5),  # Job 2 arrives at 1, duration 3, priority 5
        (3, 2, 4, 5),  # Job 3 arrives at 2, duration 4, priority 5 (Tie in priority with Job 2)
        (4, 10, 2, 1)  # Job 4 arrives at 10, duration 2, priority 1
    ]

    job_results, avg_waiting_time = simulate_queue(sample_jobs)

    print("Job Results:")
    for j_id in sorted(job_results.keys()):
        res = job_results[j_id]
        print(f"Job {j_id}: Completion Time = {res['completion_time']}, Waiting Time = {res['waiting_time']}")

    print(f"\nAverage Waiting Time: {avg_waiting_time:.2f}")