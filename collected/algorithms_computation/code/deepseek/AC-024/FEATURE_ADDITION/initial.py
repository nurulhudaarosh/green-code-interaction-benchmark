import heapq


def assign_rooms(intervals):
    """
    Assign each interval to a room so overlapping intervals never share a room.

    Args:
        intervals: list of (start, end) tuples, half-open [start, end).

    Returns:
        List[int] room_ids where room_ids[i] is the room for intervals[i].
    """
    n = len(intervals)
    if n == 0:
        return []

    # Pair each interval with its original index, then sort by start time.
    indexed = sorted(
        ((start, end, i) for i, (start, end) in enumerate(intervals)),
        key=lambda x: (x[0], x[2]),  # deterministic tie-break by original index
    )

    room_ids = [0] * n
    # Min-heap of (end_time, room_id) for rooms currently in use.
    heap = []
    next_room_id = 0

    for start, end, original_idx in indexed:
        if heap and heap[0][0] <= start:
            # Reuse the room that frees up earliest.
            _, room_id = heapq.heappop(heap)
        else:
            # Allocate a new room.
            room_id = next_room_id
            next_room_id += 1

        heapq.heappush(heap, (end, room_id))
        room_ids[original_idx] = room_id

    return room_ids


if __name__ == "__main__":
    # Example 1: overlapping intervals
    intervals1 = [(0, 30), (5, 10), (15, 20)]
    print(assign_rooms(intervals1))  # e.g. [0, 1, 1]

    # Example 2: touching intervals can share a room
    intervals2 = [(1, 5), (5, 10), (10, 15)]
    print(assign_rooms(intervals2))  # [0, 0, 0]

    # Example 3: fully overlapping
    intervals3 = [(0, 10), (1, 11), (2, 12)]
    print(assign_rooms(intervals3))  # [0, 1, 2]

    # Example 4: empty input
    print(assign_rooms([]))  # []