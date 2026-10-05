import heapq

def min_meeting_rooms_assignment(intervals: list[list[int]]) -> list[int]:
    """
    Assigns each interval to a room minimizing the number of rooms.
    Intervals that touch (e.g. end == start) can reuse the same room.

    :param intervals: List of [start, end] intervals
    :return: List of room IDs corresponding to each input interval
    """
    if not intervals:
        return []

    # Attach original index to keep track of result order
    indexed_intervals = [
        (start, end, idx) for idx, (start, end) in enumerate(intervals)
    ]
    
    # Sort primarily by start time
    indexed_intervals.sort(key=lambda x: x[0])

    # Min-heap stores tuples of (end_time, room_id)
    room_heap = []
    assignments = [0] * len(intervals)
    next_room_id = 0

    for start, end, original_idx in indexed_intervals:
        # Check if the room with the earliest end time is free
        if room_heap and room_heap[0][0] <= start:
            # Reuse the room
            _, room_id = heapq.heappop(room_heap)
        else:
            # Allocate a new room
            room_id = next_room_id
            next_room_id += 1

        # Record assignment and update heap with new end time
        assignments[original_idx] = room_id
        heapq.heappush(room_heap, (end, room_id))

    return assignments


# Example Usage:
if __name__ == "__main__":
    test_intervals = [[0, 30], [5, 10], [15, 20], [10, 15]]
    # Original intervals:
    # 0: [0, 30]  -> needs Room 0
    # 1: [5, 10]  -> needs Room 1
    # 2: [15, 20] -> can reuse Room 1 (since [10, 15] ends at 15)
    # 3: [10, 15] -> reuses Room 1 (starts at 10 after [5, 10] ends at 10)
    
    room_assignments = min_meeting_rooms_assignment(test_intervals)
    print("Room assignments for original intervals:", room_assignments)
    # Total rooms used = max(room_assignments) + 1