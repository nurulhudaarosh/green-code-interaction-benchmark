import heapq

def assign_rooms(intervals):
    """
    Assign intervals to rooms minimizing room count.

    Args:
        intervals: list of (start, end) tuples

    Returns:
        list of room IDs (ints), one per original interval
    """
    n = len(intervals)
    if n == 0:
        return []

    # (start, end, original_index)
    indexed = [(s, e, i) for i, (s, e) in enumerate(intervals)]
    # Deterministic sort: by start, then end, then original index
    indexed.sort(key=lambda x: (x[0], x[1], x[2]))

    # Min-heap of (end_time, room_id) for rooms currently occupied
    busy = []
    # Min-heap of available room IDs
    free_rooms = []
    next_room_id = 0

    room_ids = [None] * n

    for start, end, idx in indexed:
        # Free all rooms whose end_time <= start
        while busy and busy[0][0] <= start:
            _, rid = heapq.heappop(busy)
            heapq.heappush(free_rooms, rid)

        # Pick a room: smallest available, or allocate new
        if free_rooms:
            rid = heapq.heappop(free_rooms)
        else:
            rid = next_room_id
            next_room_id += 1

        room_ids[idx] = rid
        heapq.heappush(busy, (end, rid))

    return room_ids


# Example usage / test
if __name__ == "__main__":
    intervals = [(0, 30), (5, 10), (15, 20), (10, 15)]
    result = assign_rooms(intervals)
    print("Intervals:", intervals)
    print("Room assignments:", result)
    # Expected: minimal rooms = 2
    # One valid assignment: [0, 1, 0, 1] or similar with 2 rooms

    # Verify correctness
    def verify(intervals, room_ids):
        from collections import defaultdict
        rooms = defaultdict(list)
        for i, (s, e) in enumerate(intervals):
            rooms[room_ids[i]].append((s, e))
        for rid, ivs in rooms.items():
            ivs.sort()
            for j in range(1, len(ivs)):
                if ivs[j][0] < ivs[j-1][1]:
                    return False, f"Overlap in room {rid}: {ivs[j-1]} and {ivs[j]}"
        return True, "OK"

    ok, msg = verify(intervals, result)
    print("Verification:", msg)
    print("Rooms used:", max(result) + 1 if result else 0)