import heapq
from typing import List, Tuple


def assign_rooms(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """Return (number_of_rooms, room_id_for_each_interval_in_input_order)."""
    for s, e in intervals:
        if not s < e:
            raise ValueError(f"Invalid interval ({s}, {e}): start must be < end")

    n = len(intervals)
    result = [0] * n
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    busy: List[Tuple[int, int]] = []   # min-heap of (end_time, room_id)
    free: List[int] = []               # min-heap of reusable room IDs
    room_count = 0

    for i in order:
        start, end = intervals[i]

        # Release all rooms whose interval ended at or before this start.
        while busy and busy[0][0] <= start:
            _, rid = heapq.heappop(busy)
            heapq.heappush(free, rid)

        if free:
            rid = heapq.heappop(free)      # lowest available ID
        else:
            rid = room_count               # open a new room
            room_count += 1

        result[i] = rid
        heapq.heappush(busy, (end, rid))

    return room_count, result


if __name__ == "__main__":
    tests = [
        [],
        [(1, 2)],
        [(0, 30), (5, 10), (15, 20)],
        [(1, 3), (3, 5), (5, 7)],              # touching endpoints share a room
        [(1, 4), (2, 5), (3, 6), (4, 7)],
        [(7, 10), (2, 4)],
    ]
    for t in tests:
        count, rooms = assign_rooms(t)
        print(t, "->", count, rooms)

        # Verification: no two intervals in the same room overlap.
        by_room = {}
        for (s, e), r in zip(t, rooms):
            by_room.setdefault(r, []).append((s, e))
        for lst in by_room.values():
            lst.sort()
            assert all(lst[k][1] <= lst[k + 1][0] for k in range(len(lst) - 1))