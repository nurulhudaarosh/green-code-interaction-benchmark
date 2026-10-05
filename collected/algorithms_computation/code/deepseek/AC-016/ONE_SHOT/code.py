import heapq
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Job:
    job_id: int
    arrival_time: int
    burst_time: int
    priority: int
    
    def __post_init__(self):
        if self.job_id < 0:
            raise ValueError("Job ID must be non-negative")
        if self.arrival_time < 0:
            raise ValueError("Arrival time must be non-negative")
        if self.burst_time <= 0:
            raise ValueError("Burst time must be positive")


def simulate_queue(jobs: List[Job]) -> Tuple[List[Tuple[int, int, int]], float]:
    """
    Simulate non-preemptive single-server queue with priority scheduling.
    
    Returns:
        - List of tuples: (job_id, completion_time, waiting_time) for each job
        - Average waiting time
    """
    if not jobs:
        return [], 0.0
    
    # Sort jobs by arrival time for efficient processing
    sorted_jobs = sorted(jobs, key=lambda j: (j.arrival_time, j.job_id))
    
    # Priority heap: (-priority, arrival_time, job_id, burst_time)
    # Negative priority because heapq is a min-heap but we want max priority
    ready_queue = []
    
    current_time = 0
    job_index = 0
    results = []
    total_waiting_time = 0
    
    while job_index < len(sorted_jobs) or ready_queue:
        # Add all jobs that have arrived by current_time
        while (job_index < len(sorted_jobs) and 
               sorted_jobs[job_index].arrival_time <= current_time):
            job = sorted_jobs[job_index]
            heapq.heappush(ready_queue, 
                          (-job.priority, job.arrival_time, job.job_id, job.burst_time))
            job_index += 1
        
        # If no jobs ready, jump to next arrival time
        if not ready_queue:
            if job_index < len(sorted_jobs):
                current_time = sorted_jobs[job_index].arrival_time
                continue
            else:
                break
        
        # Execute highest priority job
        neg_priority, arrival_time, job_id, burst_time = heapq.heappop(ready_queue)
        
        # Job starts execution at current_time
        start_time = current_time
        completion_time = start_time + burst_time
        waiting_time = start_time - arrival_time
        
        results.append((job_id, completion_time, waiting_time))
        total_waiting_time += waiting_time
        
        # Advance time
        current_time = completion_time
    
    # Sort results by job_id for consistent output
    results.sort(key=lambda x: x[0])
    
    avg_waiting_time = total_waiting_time / len(jobs)
    
    return results, avg_waiting_time


def print_results(jobs: List[Job], results: List[Tuple[int, int, int]], 
                  avg_waiting_time: float) -> None:
    """Print simulation results in a formatted table."""
    job_dict = {job.job_id: job for job in jobs}
    
    print(f"{'Job ID':<8} {'Arrival':<8} {'Burst':<8} {'Priority':<8} "
          f"{'Completion':<12} {'Waiting':<8}")
    print("-" * 60)
    
    for job_id, completion_time, waiting_time in results:
        job = job_dict[job_id]
        print(f"{job_id:<8} {job.arrival_time:<8} {job.burst_time:<8} "
              f"{job.priority:<8} {completion_time:<12} {waiting_time:<8}")
    
    print("-" * 60)
    print(f"Average waiting time: {avg_waiting_time:.2f}")


def run_test_cases() -> None:
    """Run deterministic test cases."""
    
    print("=" * 60)
    print("Test Case 1: Basic priority scheduling")
    print("=" * 60)
    jobs1 = [
        Job(1, 0, 5, 1),
        Job(2, 1, 3, 3),
        Job(3, 2, 2, 2),
        Job(4, 4, 4, 4),
    ]
    results, avg = simulate_queue(jobs1)
    print_results(jobs1, results, avg)
    
    print("\n" + "=" * 60)
    print("Test Case 2: Same priority - tie breaking by arrival then ID")
    print("=" * 60)
    jobs2 = [
        Job(3, 0, 2, 5),
        Job(1, 0, 3, 5),
        Job(2, 1, 4, 5),
    ]
    results, avg = simulate_queue(jobs2)
    print_results(jobs2, results, avg)
    
    print("\n" + "=" * 60)
    print("Test Case 3: Idle server with gaps between arrivals")
    print("=" * 60)
    jobs3 = [
        Job(1, 0, 2, 1),
        Job(2, 10, 3, 2),
        Job(3, 15, 1, 3),
    ]
    results, avg = simulate_queue(jobs3)
    print_results(jobs3, results, avg)
    
    print("\n" + "=" * 60)
    print("Test Case 4: High priority job arrives during execution")
    print("=" * 60)
    jobs4 = [
        Job(1, 0, 10, 1),  # Low priority, long job starts at t=0
        Job(2, 2, 2, 5),   # High priority arrives at t=2 but must wait
        Job(3, 3, 1, 3),   # Medium priority arrives at t=3
    ]
    results, avg = simulate_queue(jobs4)
    print_results(jobs4, results, avg)
    
    print("\n" + "=" * 60)
    print("Test Case 5: All jobs arrive at time 0")
    print("=" * 60)
    jobs5 = [
        Job(1, 0, 4, 2),
        Job(2, 0, 3, 5),
        Job(3, 0, 2, 5),
        Job(4, 0, 1, 1),
    ]
    results, avg = simulate_queue(jobs5)
    print_results(jobs5, results, avg)


if __name__ == "__main__":
    run_test_cases()