import heapq

def min_meeting_rooms(intervals: list[list[int]]) -> list[int]:
    """
    Assigns each interval to a room minimizing total rooms used.
    Returns a list of room IDs corresponding to the original interval order.
    """
    if not intervals:
        return []

    # Store original indices to maintain output order
    # indexed_intervals format: (start, end, original_index)
    indexed_intervals = [(start, end, i) for i, (start, end) in enumerate(intervals)]
    indexed_intervals.sort(key=lambda x: x[0])

    # Min-heap stores tuples: (end_time, room_id)
    heap = []
    
    # Result array initialized to store room IDs corresponding to input indices
    room_assignments = [0] * len(intervals)
    next_room_id = 0

    for start, end, orig_idx in indexed_intervals:
        # If a room is free by the current interval's start time, reuse it
        if heap and heap[0][0] <= start:
            _, room_id = heapq.heappop(heap)
        else:
            # Otherwise, allocate a new room
            room_id = next_room_id
            next_room_id += 1

        # Push the updated availability time and room ID back into the heap
        heapq.heappush(heap, (end, room_id))
        
        # Record assignment for the original interval
        room_assignments[orig_idx] = room_id

    return room_assignments


# Example Usage
if __name__ == "__main__":
    intervals = [[0, 30], [5, 10], [15, 20], [30, 40]]
    assignments = min_meeting_rooms(intervals)
    print("Intervals:  ", intervals)
    print("Assignments:", assignments)
    print("Total Rooms:", len(set(assignments)))