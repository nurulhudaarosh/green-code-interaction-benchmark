import heapq

def solve_interval_partitioning(intervals):
    """
    Assigns every interval a room ID to minimize total rooms, avoiding overlaps,
    with deterministic tie handling (always reusing the smallest available room_id).
    
    :param intervals: List of tuples/lists [start, end]
    :return: List of room IDs corresponding to original interval positions
    """
    if not intervals:
        return []
    
    # Store intervals with their original index: (start, end, original_index)
    # Tie-break sorting by start time, then end time, then original index for determinism
    indexed_intervals = sorted(
        [(start, end, i) for i, (start, end) in enumerate(intervals)],
        key=lambda x: (x[0], x[1], x[2])
    )
    
    # Min-heap of busy rooms: (end_time, room_id)
    busy_rooms = []
    
    # Min-heap of available room IDs for reuse (ensures smallest room_id is reused first)
    free_rooms = []
    
    assignments = [0] * len(intervals)
    next_room_id = 0
    
    for start, end, orig_idx in indexed_intervals:
        # Move all rooms that have finished by `start` from busy_rooms to free_rooms
        while busy_rooms and busy_rooms[0][0] <= start:
            _, freed_room_id = heapq.heappop(busy_rooms)
            heapq.heappush(free_rooms, freed_room_id)
            
        # Reuse smallest available room_id if any free room exists
        if free_rooms:
            room_id = heapq.heappop(free_rooms)
        else:
            room_id = next_room_id
            next_room_id += 1
            
        assignments[orig_idx] = room_id
        heapq.heappush(busy_rooms, (end, room_id))
        
    return assignments


# Example Verification
if __name__ == "__main__":
    example_intervals = [[0, 10], [0, 5], [5, 7], [10, 15]]
    result = solve_interval_partitioning(example_intervals)
    print("Intervals:", example_intervals)
    print("Deterministic Room Assignments:", result)