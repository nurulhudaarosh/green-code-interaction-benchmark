import heapq
from typing import List, Tuple


def assign_rooms(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Assign each interval a room ID (0-based) so that overlapping intervals
    never share a room, using the minimum number of rooms.

    Intervals are half-open [start, end): a room is free for reuse when
    its previous interval's end <= the next interval's start.

    Returns (number_of_rooms, room_ids) where room_ids[i] corresponds to
    intervals[i] in the original input order.
    """
    n = len(intervals)
    for i, iv in enumerate(intervals):
        if len(iv) != 2:
            raise ValueError(f"Interval {i} must have exactly two elements: {iv!r}")
        if iv[0] > iv[1]:
            raise ValueError(f"Interval {i} has start > end: {iv!r}")

    # Deterministic total order: start, then end, then original index.
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    result = [-1] * n
    heap: List[Tuple[int, int]] = []  # (end_time, room_id)
    room_count = 0

    for i in order:
        start, end = intervals[i]

        if heap and heap[0][0] <= start:
            _, room = heapq.heappop(heap)   # reuse earliest-free (lowest ID on ties)
        else:
            room = room_count               # all rooms busy: open a new one
            room_count += 1

        result[i] = room
        heapq.heappush(heap, (end, room))

    return room_count, result


def _verify(intervals, room_count, rooms):
    """Check validity (no overlaps in a room) and minimality."""
    by_room = {}
    for i, r in enumerate(rooms):
        by_room.setdefault(r, []).append(intervals[i])
    for ivs in by_room.values():
        ivs.sort()
        for (s1, e1), (s2, e2) in zip(ivs, ivs[1:]):
            assert e1 <= s2, f"overlap: {(s1, e1)} and {(s2, e2)}"

    # Minimum = max simultaneous overlap (sweep line; ends before starts at ties).
    events = []
    for s, e in intervals:
        if s < e:
            events.append((s, 1))
            events.append((e, -1))
    events.sort(key=lambda x: (x[0], x[1]))
    cur = peak = 0
    for _, d in events:
        cur += d
        peak = max(peak, cur)
    # Zero-length intervals still need a room if there are no others.
    if intervals and peak == 0:
        peak = 1
    assert room_count == peak, f"not minimal: {room_count} vs {peak}"


if __name__ == "__main__":
    tests = [
        [],
        [(0, 30), (5, 10), (15, 20)],
        [(1, 3), (3, 5), (5, 7)],              # touching -> one room
        [(1, 4), (2, 5), (3, 6), (4, 7)],
        [(7, 7), (7, 7), (1, 2)],              # zero-length intervals
        [(5, 10), (0, 30), (15, 20), (0, 30)], # unsorted input, duplicates
    ]
    for t in tests:
        count, rooms = assign_rooms(t)
        _verify(t, count, rooms)
        print(f"{t}\n  -> rooms={count}, ids={rooms}")