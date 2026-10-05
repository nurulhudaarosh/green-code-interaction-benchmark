import heapq

def simulate_priority_queue(jobs):
    """
    Simulates a non-preemptive single-server priority queue.
    
    :param jobs: List of dicts/tuples representing jobs:
                 {'id': int/str, 'arrival': float/int, 'duration': float/int, 'priority': float/int}
    :return: Tuple (job_results, average_waiting_time)
    """
    # Sort initial job list by arrival time, then by job ID
    sorted_jobs = sorted(jobs, key=lambda x: (x['arrival'], x['id']))
    
    n = len(sorted_jobs)
    job_idx = 0
    current_time = 0
    
    ready_queue = []  # Heap storing (-priority, arrival, id, duration)
    results = {}
    total_waiting_time = 0

    while job_idx < n or ready_queue:
        # If queue is empty and next job arrives in the future, jump time forward
        if not ready_queue and current_time < sorted_jobs[job_idx]['arrival']:
            current_time = sorted_jobs[job_idx]['arrival']
        
        # Enqueue all jobs that have arrived by current_time
        while job_idx < n and sorted_jobs[job_idx]['arrival'] <= current_time:
            job = sorted_jobs[job_idx]
            # Max-heap for priority simulated via negative priority value
            heapq.heappush(ready_queue, (-job['priority'], job['arrival'], job['id'], job['duration']))
            job_idx += 1

        # Pop highest priority job
        neg_prio, arrival, job_id, duration = heapq.heappop(ready_queue)
        
        # Calculate timing metrics
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
    return results, avg_waiting_time


# Example Usage
if __name__ == "__main__":
    job_list = [
        {'id': 1, 'arrival': 0, 'duration': 4, 'priority': 2},
        {'id': 2, 'arrival': 1, 'duration': 3, 'priority': 5},
        {'id': 3, 'arrival': 2, 'duration': 1, 'priority': 5},
        {'id': 4, 'arrival': 10, 'duration': 2, 'priority': 1},
    ]

    res, avg_wait = simulate_priority_queue(job_list)
    
    print("Job Metrics:")
    for j_id, metrics in sorted(res.items()):
        print(f"Job {j_id} -> Completion Time: {metrics['completion_time']}, Waiting Time: {metrics['waiting_time']}")
    
    print(f"\nAverage Waiting Time: {avg_wait:.2f}")