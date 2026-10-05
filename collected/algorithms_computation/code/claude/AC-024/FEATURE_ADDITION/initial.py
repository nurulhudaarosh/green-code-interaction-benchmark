import heapq
from typing import List, Sequence, Tuple


def assign_rooms(intervals: Sequence[Tuple[int, int]]) -> List[int]:
    """Return rooms[i] = room ID for intervals[i], using the minimum number of rooms.

    Intervals are half-open [start, end): an interval may reuse a room whose
    previous interval ends at or before the new start.
    """
    n = len(intervals)
    for i, (s, e) in enumerate(intervals):
        if e < s:
            raise ValueError(f"Interval {i} has end < start: {(s, e)}")

    # Deterministic processing order: start, then end, then original index.
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    rooms: List[int] = [0] * n
    heap: List[Tuple[int, int]] = []  # (end_time, room_id)
    next_room = 0

    for i in order:
        start, end = intervals[i]
        if heap and heap[0][0] <= start:
            _, room = heapq.heappop(heap)   # reuse earliest-freed room
        else:
            room = next_room                # all rooms busy: open a new one
            next_room += 1
        rooms[i] = room
        heapq.heappush(heap, (end, room))

    return rooms


if __name__ == "__main__":
    tests = [
        [],
        [(0, 30), (5, 10), (15, 20)],
        [(1, 3), (3, 5), (5, 7)],           # touching endpoints reuse one room
        [(5, 8), (1, 4), (2, 6), (4, 7)],   # unsorted input
        [(2, 2), (2, 2), (2, 5)],           # zero-length intervals
    ]
    for t in tests:
        r = assign_rooms(t)
        print(t, "->", r, "rooms:", (max(r) + 1) if r else 0)