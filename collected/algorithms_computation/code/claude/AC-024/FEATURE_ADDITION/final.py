import heapq
from typing import Dict, List, Sequence, Tuple, Union


def assign_rooms(
    intervals: Sequence[Tuple[int, int]],
    include_summary: bool = False,
) -> Union[List[int], Dict[str, object]]:
    """Assign each half-open interval [start, end) to a room, minimizing rooms.

    include_summary=False -> returns rooms (List[int]), exactly as before.
    include_summary=True  -> returns {"rooms": [...], "operation_summary": {...}}.
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

    # Operation counters (only reported when requested).
    comparisons = reused = opened = pops = pushes = 0

    for i in order:
        start, end = intervals[i]
        if heap:
            comparisons += 1
        if heap and heap[0][0] <= start:
            _, room = heapq.heappop(heap)   # reuse earliest-freed room
            pops += 1
            reused += 1
        else:
            room = next_room                # all rooms busy: open a new one
            next_room += 1
            opened += 1
        rooms[i] = room
        heapq.heappush(heap, (end, room))
        pushes += 1

    if not include_summary:
        return rooms

    return {
        "rooms": rooms,
        "operation_summary": {
            "intervals_processed": n,
            "heap_top_comparisons": comparisons,
            "rooms_reused": reused,
            "rooms_opened": opened,
            "heap_pops": pops,
            "heap_pushes": pushes,
            "total_rooms": next_room,
            "major_operations": comparisons + pops + pushes,
        },
    }


if __name__ == "__main__":
    tests = [
        [],
        [(0, 30), (5, 10), (15, 20)],
        [(1, 3), (3, 5), (5, 7)],
        [(5, 8), (1, 4), (2, 6), (4, 7)],
        [(2, 2), (2, 2), (2, 5)],
    ]
    for t in tests:
        assert assign_rooms(t) == assign_rooms(t, include_summary=True)["rooms"]
        print(t)
        print("  default:", assign_rooms(t))
        print("  summary:", assign_rooms(t, include_summary=True)["operation_summary"])