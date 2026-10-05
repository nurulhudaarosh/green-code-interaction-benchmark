import heapq

def assign_rooms(intervals: list[list[int]]) -> list[int]:
    """
    Assigns each interval to a room such that no overlapping intervals share a room,
    minimizing total rooms used and preserving the original order.
    """
    if not intervals:
        return []

    # Attach original indices: (start, end, original_index)
    indexed_intervals = [(start, end, i) for i, (start, end) in enumerate(intervals)]
    
    # Sort primarily by start time
    indexed_intervals.sort(key=lambda x: x[0])

    # Min-heap for active rooms: (end_time, room_id)
    active_rooms = []
    
    # Min-heap for free room IDs to reuse the smallest available room ID
    available_room_ids = []
    
    room_assignments = [0] * len(intervals)
    next_new_room_id = 0

    for start, end, original_idx in indexed_intervals:
        # Free up rooms whose interval has ended at or before current start time
        while active_rooms and active_rooms[0][0] <= start:
            _, freed_room_id = heapq.heappop(active_rooms)
            heapq.heappush(available_room_ids, freed_room_id)

        # Pick the smallest available room ID or create a new one
        if available_room_ids:
            assigned_room_id = heapq.heappop(available_room_ids)
        else:
            assigned_room_id = next_new_room_id
            next_new_room_id += 1

        # Record assignment and update active rooms heap
        room_assignments[original_idx] = assigned_room_id
        heapq.heappush(active_rooms, (end, assigned_room_id))

    return room_assignments


# Example Usage:
if __name__ == "__main__":
    test_intervals = [[0, 30], [5, 10], [15, 20], [10, 30]]
    result = assign_rooms(test_intervals)
    print("Intervals:", test_intervals)
    print("Room Assignments:", result)  # Output: [0, 1, 1, 1]