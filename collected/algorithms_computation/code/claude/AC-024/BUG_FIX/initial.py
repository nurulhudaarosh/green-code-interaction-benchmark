import heapq
from typing import List, Tuple


def assign_rooms(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Assign each interval to a room so overlapping intervals never share one.

    intervals: list of (start, end) with start <= end. Intervals are treated
               as half-open [start, end), so (1, 3) and (3, 5) may share a room.
    Returns:   (number_of_rooms, rooms) where rooms[i] is the 0-based room ID
               of intervals[i].
    """
    for s, e in intervals:
        if e < s:
            raise ValueError(f"Invalid interval ({s}, {e}): end < start")

    # Deterministic processing order: by start, then end, then original index.
    order = sorted(range(len(intervals)),
                   key=lambda i: (intervals[i][0], intervals[i][1], i))

    heap: List[Tuple[int, int]] = []   # (end_time, room_id)
    rooms = [0] * len(intervals)
    next_room = 0

    for i in order:
        start, end = intervals[i]
        if heap and heap[0][0] <= start:
            _, room = heapq.heappop(heap)      # reuse the freed room
        else:
            room = next_room                   # all busy: open a new room
            next_room += 1
        rooms[i] = room
        heapq.heappush(heap, (end, room))

    return next_room, rooms


if __name__ == "__main__":
    tests = [
        [],
        [(0, 30), (5, 10), (15, 20)],
        [(1, 3), (3, 5), (5, 7)],            # touching -> one room
        [(1, 4), (2, 5), (3, 6), (4, 7)],
        [(5, 8), (1, 3), (2, 6), (6, 9)],    # unsorted input
        [(2, 2), (2, 2), (2, 3)],            # zero-length intervals
    ]
    for t in tests:
        n, r = assign_rooms(t)
        print(t, "->", n, r)

        # Validate: no two intervals in one room overlap.
        by_room = {}
        for idx, room in enumerate(r):
            by_room.setdefault(room, []).append(t[idx])
        for lst in by_room.values():
            lst.sort()
            for a, b in zip(lst, lst[1:]):
                assert a[1] <= b[0], "overlap detected"