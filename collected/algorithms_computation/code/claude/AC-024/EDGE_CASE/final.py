import heapq
from itertools import product
from typing import List, Sequence, Tuple


def assign_rooms(intervals: Sequence[Tuple[int, int]]) -> List[int]:
    """Return room IDs (0-based) for each interval in original order.

    Half-open [start, end): a room is reusable when its last interval
    ended at or before the next start. Uses the minimum number of rooms.
    Zero-length intervals occupy no time: they never use the heap and
    are given room 0.
    Tie-breaking: process order (start, end, index); reuse the free room
    with smallest (end_time, room_id); otherwise open the next new ID.
    """
    n = len(intervals)
    for s, e in intervals:
        if e < s:
            raise ValueError(f"Invalid interval ({s}, {e}): end < start")

    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    result = [0] * n
    heap: List[Tuple[int, int]] = []  # (end_time, room_id)
    next_room = 0

    for i in order:
        start, end = intervals[i]
        if start == end:
            result[i] = 0  # empty interval: conflicts with nothing
            continue
        if heap and heap[0][0] <= start:
            _, room = heapq.heappop(heap)
        else:
            room = next_room
            next_room += 1
        result[i] = room
        heapq.heappush(heap, (end, room))

    return result


def _peak_overlap(intervals) -> int:
    events = []
    for s, e in intervals:
        if s < e:
            events.append((s, 1))
            events.append((e, -1))
    events.sort()  # at equal times, -1 sorts before +1 (touching is OK)
    cur = peak = 0
    for _, d in events:
        cur += d
        peak = max(peak, cur)
    return peak


def _validate(intervals, rooms) -> None:
    """No overlaps within a room, and the room count is minimal."""
    assert len(rooms) == len(intervals)
    by_room = {}
    for (s, e), r in zip(intervals, rooms):
        if s < e:
            by_room.setdefault(r, []).append((s, e))
    for lst in by_room.values():
        lst.sort()
        for (s1, e1), (s2, e2) in zip(lst, lst[1:]):
            assert e1 <= s2, f"Overlap: {(s1, e1)} and {(s2, e2)}"
    expected_k = max(_peak_overlap(intervals), 1 if intervals else 0)
    assert len(set(rooms)) == expected_k, (len(set(rooms)), expected_k)
    assert not rooms or set(rooms) == set(range(expected_k))


def _run_tests() -> None:
    # --- Original cases (outputs corrected where noted) ---
    assert assign_rooms([]) == []
    assert assign_rooms([(1, 3)]) == [0]
    assert assign_rooms([(0, 30), (5, 10), (15, 20)]) == [0, 1, 1]
    assert assign_rooms([(1, 3), (3, 5), (5, 7)]) == [0, 0, 0]
    assert assign_rooms([(1, 4), (2, 5), (3, 6), (4, 7)]) == [0, 1, 2, 0]
    assert assign_rooms([(7, 10), (2, 4), (2, 4), (4, 7)]) == [1, 0, 1, 0]  # corrected
    assert assign_rooms([(2, 2), (2, 2), (1, 3)]) == [0, 0, 0]              # corrected
    assert assign_rooms([(5, 5), (5, 5)]) == [0, 0]

    # --- Worst-case-like structures ---
    n = 50_000
    big = 10 ** 9

    # 1. All mutually overlapping: heap grows to n.
    t = [(i, big) for i in range(n)]
    r = assign_rooms(t)
    assert r == list(range(n))
    _validate(t, r)

    # 2. Same intervals, reverse-sorted input.
    t = [(n - 1 - i, big) for i in range(n)]
    r = assign_rooms(t)
    assert r == [n - 1 - i for i in range(n)]
    _validate(t, r)

    # 3. All identical: ties resolved purely by original index.
    t = [(0, 1)] * n
    r = assign_rooms(t)
    assert r == list(range(n))
    _validate(t, r)

    # 4. Touching chain: one room, heap size 1.
    t = [(i, i + 1) for i in range(n)]
    r = assign_rooms(t)
    assert r == [0] * n
    _validate(t, r)

    # 5. Staircase (i, i+k): heap stays at size k, constant pop+push.
    k = 100
    t = [(i, i + k) for i in range(n)]
    r = assign_rooms(t)
    assert r == [i % k for i in range(n)]
    _validate(t, r)

    # 6. Two waves with equal end times: room-ID tie-break decides everything.
    m = 20_000
    t = [(0, 10)] * m + [(10, 20)] * m
    r = assign_rooms(t)
    assert r == list(range(m)) + list(range(m))
    _validate(t, r)

    # 7. Many zero-length intervals mixed with a long one.
    t = [(5, 5)] * 1000 + [(0, 10)]
    r = assign_rooms(t)
    assert r == [0] * 1001
    _validate(t, r)

    # --- Exhaustive small check (deterministic) ---
    pairs = [(s, e) for s in range(4) for e in range(s, 4)]
    for size in range(1, 4):
        for combo in product(pairs, repeat=size):
            t = list(combo)
            _validate(t, assign_rooms(t))
            assert assign_rooms(t) == assign_rooms(list(t))  # deterministic

    # Invalid input
    try:
        assign_rooms([(3, 1)])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


if __name__ == "__main__":
    _run_tests()
    print("All tests passed.")