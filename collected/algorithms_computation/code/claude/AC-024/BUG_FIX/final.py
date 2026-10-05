import heapq
from itertools import product
from typing import List, Tuple


def assign_rooms(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Assign each interval to a room so overlapping intervals never share one.

    Intervals are half-open [start, end): (1, 3) and (3, 5) may share a room.
    Empty intervals (start == end) occupy no time, so they never need their
    own room; they are placed in room 0.

    Returns (number_of_rooms, rooms), rooms[i] being the 0-based room ID of
    intervals[i]. Ties: sort by (start, end, index); among rooms freeing at the
    same time, the lowest room ID is reused.
    """
    for s, e in intervals:
        if e < s:
            raise ValueError(f"Invalid interval ({s}, {e}): end < start")

    # Only non-empty intervals compete for rooms.
    order = sorted(
        (i for i, (s, e) in enumerate(intervals) if s < e),
        key=lambda i: (intervals[i][0], intervals[i][1], i),
    )

    heap: List[Tuple[int, int]] = []   # (end_time, room_id)
    rooms = [0] * len(intervals)       # empty intervals default to room 0
    next_room = 0

    for i in order:
        start, end = intervals[i]
        if heap and heap[0][0] <= start:
            _, room = heapq.heappop(heap)
        else:
            room = next_room
            next_room += 1
        rooms[i] = room
        heapq.heappush(heap, (end, room))

    count = max(next_room, 1 if intervals else 0)
    return count, rooms


def peak_overlap(intervals: List[Tuple[int, int]], lo: int, hi: int) -> int:
    return max(
        (sum(1 for s, e in intervals if s <= t < e) for t in range(lo, hi + 1)),
        default=0,
    )


def check(intervals: List[Tuple[int, int]], lo: int = 0, hi: int = 3) -> None:
    n, rooms = assign_rooms(intervals)
    assert len(rooms) == len(intervals)
    assert n == max(peak_overlap(intervals, lo, hi), 1 if intervals else 0)
    by_room = {}
    for idx, r in enumerate(rooms):
        assert 0 <= r < max(n, 1)
        if intervals[idx][0] < intervals[idx][1]:        # skip empty intervals
            by_room.setdefault(r, []).append(intervals[idx])
    for lst in by_room.values():
        lst.sort()
        for a, b in zip(lst, lst[1:]):
            assert a[1] <= b[0], f"overlap in {intervals}"


if __name__ == "__main__":
    print(assign_rooms([(1, 3), (2, 2)]))                 # (1, [0, 0])  (was (2, [0, 1]))
    print(assign_rooms([(0, 30), (5, 10), (15, 20)]))     # (2, [0, 1, 1])
    print(assign_rooms([(1, 4), (2, 5), (3, 6), (4, 7)])) # (3, [0, 1, 2, 0])
    print(assign_rooms([(2, 2), (2, 2), (2, 3)]))         # (1, [0, 0, 0])
    print(assign_rooms([]))                               # (0, [])

    # Exhaustive deterministic check: every list of up to 3 intervals on 0..3.
    pairs = [(s, e) for s in range(4) for e in range(s, 4)]
    for k in range(4):
        for combo in product(pairs, repeat=k):
            check(list(combo))
    print("all checks passed")