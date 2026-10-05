import heapq


def assign_rooms(intervals):
    """
    intervals: list of (start, end, original_index)
    returns: list of room IDs indexed by original_index
    """
    n = len(intervals)
    if n == 0:
        return []

    # Sort by start time; tie-break by end time, then original index for determinism
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], intervals[i][2]))

    result = [None] * n
    # Min-heap of (end_time, room_id)
    heap = []
    next_room_id = 0

    for i in order:
        start, end, orig_idx = intervals[i]

        if heap and heap[0][0] <= start:
            # Reuse the room that frees up earliest
            end_time, room_id = heapq.heappop(heap)
        else:
            # Allocate a new room
            room_id = next_room_id
            next_room_id += 1

        result[orig_idx] = room_id
        heapq.heappush(heap, (end, room_id))

    return result


# ---------- Demonstration ----------
if __name__ == "__main__":
    # Example: (start, end, original_index)
    intervals = [
        (1, 4, 0),
        (2, 5, 1),
        (7, 9, 2),
        (3, 6, 3),
        (8, 10, 4),
        (4, 7, 5),
    ]

    rooms = assign_rooms(intervals)
    print("Room assignments (by original index):")
    for i, r in enumerate(rooms):
        s, e, _ = intervals[i]
        print(f"  Interval {i}: [{s}, {e}) -> Room {r}")

    print(f"\nMinimum rooms needed: {max(rooms) + 1}")