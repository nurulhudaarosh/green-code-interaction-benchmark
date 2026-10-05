import heapq
import math
from typing import Dict, List, Tuple, Union


def assign_rooms_with_summary(
    intervals: List[List[int]], include_summary: bool = True
) -> Union[List[int], Tuple[List[int], Dict[str, Union[int, float]]]]:
    """Assigns intervals to rooms with minimum total rooms used.

    Args:
        intervals: List of [start, end] pairs.
        include_summary: If True, returns (assignments, operation_summary). If
          False, returns only assignments to match the original API contract.

    Returns:
        List of room assignments, or a tuple containing (assignments,
        operation_summary_dict).
    """
    if not intervals:
        summary = {
            "total_intervals": 0,
            "sort_comparisons_bound": 0,
            "rooms_freed_count": 0,
            "rooms_reused_count": 0,
            "new_rooms_created": 0,
            "heap_operations_count": 0,
        }
        return ([], summary) if include_summary else []

    n = len(intervals)

    # Attach original indices: (start, end, original_index)
    indexed_intervals = [(start, end, i) for i, (start, end) in enumerate(intervals)]

    # Sort intervals by start time
    indexed_intervals.sort(key=lambda x: x[0])

    active_rooms: List[Tuple[int, int]] = []  # Min-heap of (end_time, room_id)
    available_room_ids: List[int] = []  # Min-heap of free room_ids

    room_assignments = [0] * n
    next_new_room_id = 0

    # Tracking metrics for operation summary
    rooms_freed_count = 0
    rooms_reused_count = 0
    heap_ops = 0

    for start, end, original_idx in indexed_intervals:
        # Release rooms that end at or before current start time
        while active_rooms and active_rooms[0][0] <= start:
            _, freed_room_id = heapq.heappop(active_rooms)
            heap_ops += 1

            heapq.heappush(available_room_ids, freed_room_id)
            heap_ops += 1

            rooms_freed_count += 1

        # Select room ID
        if available_room_ids:
            assigned_room_id = heapq.heappop(available_room_ids)
            heap_ops += 1
            rooms_reused_count += 1
        else:
            assigned_room_id = next_new_room_id
            next_new_room_id += 1

        # Assign room and track active end time
        room_assignments[original_idx] = assigned_room_id
        heapq.heappush(active_rooms, (end, assigned_room_id))
        heap_ops += 1

    if not include_summary:
        return room_assignments

    operation_summary = {
        "total_intervals": n,
        "sort_comparisons_bound": round(n * math.log2(n), 2) if n > 1 else 0,
        "rooms_freed_count": rooms_freed_count,
        "rooms_reused_count": rooms_reused_count,
        "new_rooms_created": next_new_room_id,
        "heap_operations_count": heap_ops,
    }

    return room_assignments, operation_summary


# Demonstration
if __name__ == "__main__":
    test_intervals = [[0, 30], [5, 10], [15, 20], [10, 30]]

    # 1. Original behavior (without summary)
    assignments_only = assign_rooms_with_summary(
        test_intervals, include_summary=False
    )
    print("Original API Output:", assignments_only)

    # 2. Enhanced behavior (with operation summary)
    assignments, summary = assign_rooms_with_summary(
        test_intervals, include_summary=True
    )
    print("\nEnhanced Output:")
    print("Room Assignments:", assignments)
    print("Operation Summary:")
    for k, v in summary.items():
        print(f"  - {k}: {v}")