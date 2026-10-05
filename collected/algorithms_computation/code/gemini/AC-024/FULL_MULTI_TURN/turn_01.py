import heapq

def solve_interval_partitioning(intervals):
    """
    Assigns every interval a room ID to minimize total rooms and avoid overlaps.
    
    :param intervals: List of tuples/lists [start, end]
    :return: List of room IDs corresponding to original interval positions
    """
    if not intervals:
        return []
    
    # Store intervals with their original index: (start, end, original_index)
    indexed_intervals = [(start, end, i) for i, (start, end) in enumerate(intervals)]
    
    # Sort primarily by start time
    indexed_intervals.sort(key=lambda x: x[0])
    
    # Min-heap storing tuples: (end_time, room_id)
    heap = []
    
    # Track room assignments for the original ordering
    assignments = [0] * len(intervals)
    next_room_id = 0
    
    for start, end, orig_idx in indexed_intervals:
        # Reuse room if the earliest available room ends at or before current start
        if heap and heap[0][0] <= start:
            _, room_id = heapq.heappop(heap)
        else:
            room_id = next_room_id
            next_room_id += 1
            
        assignments[orig_idx] = room_id
        heapq.heappush(heap, (end, room_id))
        
    return assignments


# Example Usage
if __name__ == "__main__":
    example_intervals = [[0, 30], [5, 10], [15, 20], [5, 15]]
    result = solve_interval_partitioning(example_intervals)
    print("Intervals:", example_intervals)
    print("Room Assignments:", result)