import heapq


def assign_rooms(intervals):
    """
    Assign each interval to a room so that overlapping intervals never share a room.
    Reuse a room when its previous interval ends at or before the next start.
    Minimize the number of rooms.

    Args:
        intervals: list of [start, end] pairs (half-open: [start, end))

    Returns:
        list of room IDs (0-indexed), one per input interval, in original order.
    """
    n = len(intervals)
    if n == 0:
        return []

    # Sort by start time; tie-break by original index for determinism.
    order = sorted(range(n), key=lambda i: (intervals[i][0], i))

    room_ids = [None] * n

    # Min-heap of (end_time, room_id) for rooms currently occupied.
    active = []
    # Min-heap of available (freed) room IDs.
    available = []
    next_room_id = 0

    for idx in order:
        start, end = intervals[idx]

        # Free rooms whose intervals have ended (end <= start).
        while active and active[0][0] <= start:
            _, freed_room = heapq.heappop(active)
            heapq.heappush(available, freed_room)

        # Pick the smallest available room, or open a new one.
        if available:
            room = heapq.heappop(available)
        else:
            room = next_room_id
            next_room_id += 1

        room_ids[idx] = room
        heapq.heappush(active, (end, room))

    return room_ids


if __name__ == "__main__":
    # Example 1
    intervals1 = [[0, 30], [5, 10], [15, 20]]
    print(assign_rooms(intervals1))  # e.g. [0, 1, 2] (3 rooms needed)

    # Example 2 (reuse case)
    intervals2 = [[7, 10], [2, 4], [1, 3], [5, 8]]
    print(assign_rooms(intervals2))  # 2 rooms suffice

    # Example 3 (touching intervals reuse the same room)
    intervals3 = [[1, 2], [2, 3], [3, 4]]
    print(assign_rooms(intervals3))  # all share room 0

    # Example 4 (empty)
    print(assign_rooms([]))  # []