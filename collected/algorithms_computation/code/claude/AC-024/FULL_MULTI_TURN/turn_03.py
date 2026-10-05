import heapq
from typing import Dict, List, Tuple, Union


def assign_rooms(
    intervals: List[Tuple[int, int]],
    include_summary: bool = False,
) -> Union[List[int], Dict[str, object]]:
    """Assign each interval a room ID using the minimum number of rooms.

    Default (include_summary=False): returns rooms, a list where rooms[i] is
    the 0-based room ID for intervals[i].

    include_summary=True: returns {"rooms": rooms, "operation_summary": {...}}.

    A room is reusable when its last interval's end <= the next start.
    Ties: earliest-available room, then lowest room ID (heap tuple ordering).
    """
    for s, e in intervals:
        if e < s:
            raise ValueError(f"Invalid interval ({s}, {e}): end must be >= start")

    n = len(intervals)
    result = [0] * n
    order = sorted(range(n), key=lambda i: (intervals[i][0], intervals[i][1], i))

    heap: List[Tuple[int, int]] = []  # (available_at, room_id)
    room_count = 0
    reused = 0
    pops = 0
    pushes = 0

    for i in order:
        start, end = intervals[i]
        if heap and heap[0][0] <= start:
            _, rid = heapq.heappop(heap)
            pops += 1
            reused += 1
        else:
            rid = room_count
            room_count += 1
        result[i] = rid
        heapq.heappush(heap, (end, rid))
        pushes += 1

    if not include_summary:
        return result

    return {
        "rooms": result,
        "operation_summary": {
            "intervals_processed": n,
            "rooms_reused": reused,
            "rooms_opened": room_count,
            "heap_pops": pops,
            "heap_pushes": pushes,
            "total_major_operations": n + pops + pushes,
        },
    }


if __name__ == "__main__":
    cases = {
        "defect example": ([(0, 5), (1, 3), (6, 8)], [0, 1, 1]),
        "empty": ([], []),
        "single": ([(1, 2)], [0]),
        "touching": ([(1, 3), (3, 5), (5, 7)], [0, 0, 0]),
        "chain": ([(1, 4), (2, 5), (3, 6), (4, 7)], [0, 1, 2, 0]),
        "unsorted input": ([(7, 10), (2, 4)], [0, 0]),
        "nested": ([(0, 30), (5, 10), (15, 20)], [0, 1, 1]),
        "zero-length": ([(2, 2), (2, 2)], [0, 0]),
    }
    for name, (data, expected) in cases.items():
        plain = assign_rooms(data)
        assert plain == expected, (name, plain, expected)

        full = assign_rooms(data, include_summary=True)
        assert full["rooms"] == plain          # feature never alters the result
        s = full["operation_summary"]
        assert s["rooms_opened"] == (max(plain) + 1 if plain else 0)
        assert s["rooms_reused"] + s["rooms_opened"] == len(data)
        assert assign_rooms(data, include_summary=True) == full  # deterministic
        print(f"{name}: {plain} | {s}")