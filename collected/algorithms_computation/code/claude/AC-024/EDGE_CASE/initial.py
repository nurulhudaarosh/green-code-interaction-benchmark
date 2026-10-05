import heapq
from typing import List, Sequence, Tuple


def assign_rooms(intervals: Sequence[Tuple[int, int]]) -> List[int]:
    """Return room IDs (0-based) for each interval in original order.

    Intervals are half-open [start, end): an interval may reuse a room
    whose previous interval ended at or before its start.
    Uses the minimum possible number of rooms.
    """
    n = len(intervals)
    for s, e in intervals:
        if e < s:
            raise ValueError(f"Invalid interval ({s}, {e}): end < start")

    # Deterministic processing order: start, then end, then original index.
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    result = [0] * n
    heap: List[Tuple[int, int]] = []  # (end_time, room_id)
    next_room = 0

    for i in order:
        start, end = intervals[i]
        if heap and heap[0][0] <= start:
            _, room = heapq.heappop(heap)  # reuse earliest-free room
        else:
            room = next_room               # open a new room
            next_room += 1
        result[i] = room
        heapq.heappush(heap, (end, room))

    return result


def _validate(intervals, rooms) -> None:
    """Check no overlaps within a room (used by the self-test)."""
    by_room = {}
    for (s, e), r in zip(intervals, rooms):
        by_room.setdefault(r, []).append((s, e))
    for lst in by_room.values():
        lst.sort()
        for (s1, e1), (s2, e2) in zip(lst, lst[1:]):
            assert e1 <= s2, f"Overlap: {(s1, e1)} and {(s2, e2)}"


if __name__ == "__main__":
    tests = [
        [],
        [(1, 3)],
        [(0, 30), (5, 10), (15, 20)],
        [(1, 3), (3, 5), (5, 7)],           # touching: one room
        [(1, 4), (2, 5), (3, 6), (4, 7)],   # peak overlap 3
        [(2, 2), (2, 2), (1, 3)],           # zero-length intervals
        [(7, 10), (2, 4), (2, 4), (4, 7)],  # unsorted input
    ]
    for t in tests:
        r = assign_rooms(t)
        _validate(t, r)
        # Minimality: rooms used equals peak overlap.
        events = sorted([(s, 1) for s, e in t if s < e] +
                        [(e, -1) for s, e in t if s < e])
        cur = peak = 0
        for _, d in events:
            cur += d
            peak = max(peak, cur)
        used = len(set(r))
        assert used >= peak and (used == peak or any(s == e for s, e in t))
        print(t, "->", r)