import heapq

def min_meeting_rooms(intervals: list[list[int]]) -> list[int]:
    """
    Assigns each interval to a room minimizing total rooms used.
    Uses deterministic tie handling for available room reuse.
    Returns a list of room IDs corresponding to the original interval order.
    """
    if not intervals:
        return []

    # Store original indices to preserve input order
    # Format: (start, end, original_index)
    indexed_intervals = sorted(
        ((start, end, i) for i, (start, end) in enumerate(intervals)),
        key=lambda x: (x[0], x[1], x[2])  # Deterministic sorting tie-breaker
    )

    # Min-heap of currently occupied rooms: (end_time, room_id)
    occupied_heap = []
    
    # Min-heap of available room IDs (keyed by room_id for deterministic reuse)
    available_rooms = []
    
    room_assignments = [0] * len(intervals)
    next_room_id = 0

    for start, end, orig_idx in indexed_intervals:
        # Free up all rooms that have ended at or before current start time
        while occupied_heap and occupied_heap[0][0] <= start:
            _, freed_room_id = heapq.heappop(occupied_heap)
            heapq.heappush(available_rooms, freed_room_id)

        # Reuse the available room with the lowest ID, or create a new one
        if available_rooms:
            room_id = heapq.heappop(available_rooms)
        else:
            room_id = next_room_id
            next_room_id += 1

        # Mark room as occupied until current interval's end time
        heapq.heappush(occupied_heap, (end, room_id))
        
        # Assign room ID to original interval index
        room_assignments[orig_idx] = room_id

    return room_assignments


# Verification
if __name__ == "__main__":
    test_intervals = [[0, 10], [0, 10], [10, 20], [10, 20]]
    assignments = min_meeting_rooms(test_intervals)
    print("Intervals:  ", test_intervals)
    print("Assignments:", assignments)  # Expected: [0, 1, 0, 1]