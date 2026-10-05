import heapq

def simulate_priority_queue(jobs):
    """
    Simulates a non-preemptive single-server priority queue.
    
    Parameters:
        jobs (list of tuple): List of jobs formatted as (job_id, arrival_time, burst_time, priority)
        
    Returns:
        tuple: (results, average_waiting_time)
            - results: List of tuples (job_id, completion_time, waiting_time) sorted by job_id
            - average_waiting_time: Float representing the average wait time across all jobs
    """
    if not jobs:
        return [], 0.0

    # Sort jobs by arrival time, then by job_id
    sorted_jobs = sorted(jobs, key=lambda x: (x[1], x[0]))
    
    ready_heap = []
    results = []
    
    current_time = 0
    job_idx = 0
    num_jobs = len(sorted_jobs)
    
    while job_idx < num_jobs or ready_heap:
        # Push all jobs that have arrived by current_time into the heap
        while job_idx < num_jobs and sorted_jobs[job_idx][1] <= current_time:
            job_id, arrival_time, burst_time, priority = sorted_jobs[job_idx]
            # Max priority via negative priority value
            heapq.heappush(ready_heap, (-priority, arrival_time, job_id, burst_time))
            job_idx += 1
            
        # If no jobs are ready, jump time to the next available job arrival
        if not ready_heap:
            current_time = sorted_jobs[job_idx][1]
            continue
            
        # Get the next job to execute
        neg_priority, arrival_time, job_id, burst_time = heapq.heappop(ready_heap)
        
        # Calculate completion and waiting times
        start_time = max(current_time, arrival_time)
        completion_time = start_time + burst_time
        waiting_time = start_time - arrival_time
        
        results.append((job_id, completion_time, waiting_time))
        current_time = completion_time

    # Sort results by job_id for clean output presentation
    results.sort(key=lambda x: x[0])
    
    total_waiting_time = sum(w for _, _, w in results)
    avg_waiting_time = total_waiting_time / num_jobs
    
    return results, avg_waiting_time


# Example Usage & Verification:
if __name__ == "__main__":
    # Format: (job_id, arrival_time, burst_time, priority)
    job_list = [
        (1, 0, 5, 2),
        (2, 2, 3, 5),  # High priority, arrives at t=2
        (3, 2, 4, 3),  # Medium priority, arrives at t=2
        (4, 10, 2, 1)  # Arrives after idle period
    ]
    
    job_results, avg_wait = simulate_priority_queue(job_list)
    
    print("Job Results (job_id, completion_time, waiting_time):")
    for res in job_results:
        print(f"Job {res[0]}: Completion Time = {res[1]}, Waiting Time = {res[2]}")
        
    print(f"\nAverage Waiting Time: {avg_wait:.2f}")