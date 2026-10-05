import heapq
from typing import List, Tuple, Dict, Any, Union


def assign_rooms(
    intervals: List[Tuple[int, int]],
    include_operation_summary: bool = False,
) -> Union[List[int], Dict[str, Any]]:
    """
    Minimum Room Assignment (interval partitioning).

    Assign every interval [start, end) to a room so overlapping intervals
    never share a room. A room may be reused when its previous interval
    ends at or before the next interval's start (previous_end <= next_start).
    Minimize the number of rooms and return the room ID for every original
    interval, preserving input order.

    Args:
        intervals: list of (start, end) tuples, half-open [start, end).
        include_operation_summary:
            If False (default), return only the room_ids list (original behavior).
            If True, return a dict with 'room_ids' and 'operation_summary'.

    Returns:
        include_operation_summary=False:
            List[int] room_ids, where room_ids[i] is the room for intervals[i].

        include_operation_summary=True:
            {
              "room_ids": List[int],
              "operation_summary": {
                  "total_operations": int,       # == n (one major decision per interval)
                  "reuse_decisions": int,        # intervals that reused an existing room
                  "allocation_decisions": int,   # intervals that required a new room
                  "rooms_used": int,             # total distinct rooms allocated
              }
            }

    Algorithm:
        1. Pair each interval with its original index; sort by (start, original_index).
        2. Min-heap of (end_time, room_id) for rooms currently in use.
        3. For each interval in sorted order:
             - If heap[0].end <= start: pop and reuse that room (reuse decision).
             - Else: allocate a new room (allocation decision).
             - Push (end, room_id); record room_ids[original_index] = room_id.
        4. Return room_ids (and optionally the operation summary).

    Determinism: sort key (start, original_index) is a total order; heap ops
    are deterministic; summary is derived solely from the input.

    Complexity: O(n log n) time, O(n) space.
    Standard library only. No randomness, network, APIs, or external services.
    """
    n = len(intervals)

    # Empty input — preserve backward-compatible behavior.
    if n == 0:
        if include_operation_summary:
            return {
                "room_ids": [],
                "operation_summary": {
                    "total_operations": 0,
                    "reuse_decisions": 0,
                    "allocation_decisions": 0,
                    "rooms_used": 0,
                },
            }
        return []

    # Pair each interval with its original index; deterministic sort.
    indexed = sorted(
        ((start, end, i) for i, (start, end) in enumerate(intervals)),
        key=lambda x: (x[0], x[2]),  # tie-break by original index
    )

    room_ids = [0] * n
    heap = []                 # (end_time, room_id)
    next_room_id = 0
    reuse_decisions = 0
    allocation_decisions = 0

    for start, end, original_idx in indexed:
        if heap and heap[0][0] <= start:
            # Major operation: reuse the earliest-freeing room.
            _, room_id = heapq.heappop(heap)
            reuse_decisions += 1
        else:
            # Major operation: allocate a new room.
            room_id = next_room_id
            next_room_id += 1
            allocation_decisions += 1

        heapq.heappush(heap, (end, room_id))
        room_ids[original_idx] = room_id

    if not include_operation_summary:
        return room_ids  # original behavior, unchanged

    return {
        "room_ids": room_ids,
        "operation_summary": {
            "total_operations": n,
            "reuse_decisions": reuse_decisions,
            "allocation_decisions": allocation_decisions,
            "rooms_used": next_room_id,
        },
    }


if __name__ == "__main__":
    # ---- Original behavior (feature disabled) ----
    print(assign_rooms([(0, 30), (5, 10), (15, 20)]))       # [0, 1, 1]
    print(assign_rooms([(1, 5), (5, 10), (10, 15)]))        # [0, 0, 0]
    print(assign_rooms([(0, 10), (1, 11), (2, 12)]))        # [0, 1, 2]
    print(assign_rooms([]))                                  # []

    # ---- New feature enabled ----
    print(assign_rooms([(0, 30), (5, 10), (15, 20)], include_operation_summary=True))
    # {
    #   'room_ids': [0, 1, 1],
    #   'operation_summary': {
    #       'total_operations': 3,
    #       'reuse_decisions': 1,
    #       'allocation_decisions': 2,
    #       'rooms_used': 2,
    #   }
    # }

    print(assign_rooms([], include_operation_summary=True))
    # {
    #   'room_ids': [],
    #   'operation_summary': {
    #       'total_operations': 0,
    #       'reuse_decisions': 0,
    #       'allocation_decisions': 0,
    #       'rooms_used': 0,
    #   }
    # }