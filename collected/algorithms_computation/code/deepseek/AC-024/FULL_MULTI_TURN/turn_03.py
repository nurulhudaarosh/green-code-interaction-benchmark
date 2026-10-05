from heapq import heappush, heappop
from typing import List, Union, Dict, Any


def assign_rooms(
    intervals: List[List[int]],
    include_summary: bool = False,
) -> Union[List[int], Dict[str, Any]]:
    """
    Minimum Room Assignment.

    Assign every interval to a room so overlapping intervals never share a
    room. A room is reusable iff its previous interval ends at or before the
    next interval's start (prev_end <= next_start). Minimize the number of
    rooms and return the room ID for every original interval.

    Determinism:
      - Intervals are sorted by (start, end, original_index).
      - The min-heap is keyed by (end_time, room_id), so ties in availability
        are broken by smallest room_id.

    Args:
        intervals: List of [start, end] pairs (start < end).
        include_summary: If False (default), returns the original plain list
            of room IDs (unchanged behavior). If True, returns a dict with
            'rooms' and a deterministic 'operation_summary'.

    Returns:
        - include_summary=False: List[int] of room IDs aligned with input order.
        - include_summary=True: dict with keys 'rooms' and 'operation_summary'.
    """
    n = len(intervals)
    if n == 0:
        if include_summary:
            return {
                "rooms": [],
                "operation_summary": {
                    "sort_operations": 0,
                    "reuse_decisions": 0,
                    "allocate_decisions": 0,
                    "total_decisions": 0,
                    "rooms_used": 0,
                },
            }
        return []

    # Deterministic sort: start, then end, then original index.
    indexed = [(s, e, i) for i, (s, e) in enumerate(intervals)]
    indexed.sort(key=lambda x: (x[0], x[1], x[2]))

    result = [0] * n
    heap = []              # min-heap of (end_time, room_id)
    next_room_id = 0

    reuse_decisions = 0
    allocate_decisions = 0

    for start, end, orig_idx in indexed:
        if heap and heap[0][0] <= start:
            # Earliest-freeing room; ties broken by smallest room_id.
            _, room_id = heappop(heap)
            reuse_decisions += 1
        else:
            # No reusable room; allocate a new one.
            room_id = next_room_id
            next_room_id += 1
            allocate_decisions += 1

        result[orig_idx] = room_id
        heappush(heap, (end, room_id))

    if include_summary:
        return {
            "rooms": result,
            "operation_summary": {
                "sort_operations": 1,
                "reuse_decisions": reuse_decisions,
                "allocate_decisions": allocate_decisions,
                "total_decisions": reuse_decisions + allocate_decisions,
                "rooms_used": next_room_id,
            },
        }
    return result


if __name__ == "__main__":
    # --- Original behavior (feature disabled) is unchanged ---
    print(assign_rooms([[0, 2], [0, 2], [2, 3]]))
    # [0, 1, 0]

    print(assign_rooms([[1, 3], [1, 3], [3, 5], [3, 5]]))
    # [0, 1, 0, 1]

    print(assign_rooms([[1, 3], [3, 5], [5, 7]]))
    # [0, 0, 0]

    print(assign_rooms([[1, 10], [2, 3], [4, 5]]))
    # [0, 1, 1]

    print(assign_rooms([]))
    # []

    # --- New feature enabled ---
    print(assign_rooms([[0, 2], [0, 2], [2, 3]], include_summary=True))
    # {'rooms': [0, 1, 0],
    #  'operation_summary': {'sort_operations': 1,
    #                        'reuse_decisions': 1,
    #                        'allocate_decisions': 2,
    #                        'total_decisions': 3,
    #                        'rooms_used': 2}}

    print(assign_rooms([[1, 3], [1, 3], [3, 5], [3, 5]], include_summary=True))
    # {'rooms': [0, 1, 0, 1],
    #  'operation_summary': {'sort_operations': 1,
    #                        'reuse_decisions': 2,
    #                        'allocate_decisions': 2,
    #                        'total_decisions': 4,
    #                        'rooms_used': 2}}

    print(assign_rooms([[1, 3], [3, 5], [5, 7]], include_summary=True))
    # {'rooms': [0, 0, 0],
    #  'operation_summary': {'sort_operations': 1,
    #                        'reuse_decisions': 2,
    #                        'allocate_decisions': 1,
    #                        'total_decisions': 3,
    #                        'rooms_used': 1}}

    print(assign_rooms([], include_summary=True))
    # {'rooms': [],
    #  'operation_summary': {'sort_operations': 0,
    #                        'reuse_decisions': 0,
    #                        'allocate_decisions': 0,
    #                        'total_decisions': 0,
    #                        'rooms_used': 0}}

    # --- Determinism checks ---
    for _ in range(5):
        assert assign_rooms([[0, 2], [0, 2], [2, 3]]) == [0, 1, 0]
        assert assign_rooms([[0, 2], [0, 2], [2, 3]], include_summary=True) == {
            "rooms": [0, 1, 0],
            "operation_summary": {
                "sort_operations": 1,
                "reuse_decisions": 1,
                "allocate_decisions": 2,
                "total_decisions": 3,
                "rooms_used": 2,
            },
        }