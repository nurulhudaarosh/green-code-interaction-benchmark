import heapq
from typing import List, Tuple


def assign_rooms(intervals: List[Tuple[int, int]]) -> List[int]:
    """Return rooms[i] = room ID (0-based) for intervals[i], using the minimum number of rooms.

    A room is reusable when its last interval's end <= the next start.
    Ties: the room with the earliest availability is reused; equal
    availability breaks by lowest room ID (heap tuple ordering).
    """
    for s, e in intervals:
        if e < s:
            raise ValueError(f"Invalid interval ({s}, {e}): end must be >= start")

    n = len(intervals)
    result = [0] * n
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    heap: List[Tuple[int, int]] = []  # (available_at, room_id) for every room opened
    room_count = 0

    for i in order:
        start, end = intervals[i]
        if heap and heap[0][0] <= start:
            _, rid = heapq.heappop(heap)   # earliest-available room, lowest ID on ties
        else:
            rid = room_count               # all rooms busy: open a new one
            room_count += 1
        result[i] = rid
        heapq.heappush(heap, (end, rid))

    return result


if __name__ == "__main__":
    cases = {
        "defect example": ([(0, 5), (1, 3), (6, 8)], [0, 1, 1]),
        "empty": ([], []),
        "single": ([(1, 2)], [0]),
        "touching": ([(1, 3), (3, 5), (5, 7)], [0, 0, 0]),
        "chain": ([(1, 4), (2, 5), (3, 6), (4, 7)], [0, 1, 2, 0]),
        "unsorted input": ([(7, 10), (2, 4)], [0, 0]),
        "nested": ([(0, 30), (5, 10), (15, 20)], [0, 1, 1]),
    }
    for name, (data, expected) in cases.items():
        got = assign_rooms(data)
        assert got == expected, (name, got, expected)

        # Validity: no overlaps within a room.
        by_room = {}
        for (s, e), r in zip(data, got):
            by_room.setdefault(r, []).append((s, e))
        for lst in by_room.values():
            lst.sort()
            assert all(a[1] <= b[0] for a, b in zip(lst, lst[1:]))
        print(f"{name}: {data} -> {got}")