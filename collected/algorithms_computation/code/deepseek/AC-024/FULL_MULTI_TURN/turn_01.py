from heapq import heappush, heappop
from typing import List


def assign_rooms(intervals: List[List[int]]) -> List[int]:
    """
    Assign a room ID to each interval, minimizing the number of rooms.

    Args:
        intervals: List of [start, end] pairs (start < end).

    Returns:
        List of room IDs aligned with the input order (0-indexed).
    """
    n = len(intervals)
    if n == 0:
        return []

    # (start, end, original_index)
    indexed = [(s, e, i) for i, (s, e) in enumerate(intervals)]
    indexed.sort(key=lambda x: (x[0], x[1]))

    result = [0] * n
    # Min-heap of (end_time, room_id) for rooms currently in use
    heap = []
    next_room_id = 0

    for start, end, orig_idx in indexed:
        if heap and heap[0][0] <= start:
            # Reuse the room that frees up earliest
            _, room_id = heappop(heap)
        else:
            # Allocate a new room
            room_id = next_room_id
            next_room_id += 1

        result[orig_idx] = room_id
        heappush(heap, (end, room_id))

    return result


if __name__ == "__main__":
    # Example: overlapping intervals
    intervals = [[1, 4], [2, 5], [7, 9], [3, 6], [8, 10]]
    print("Intervals:", intervals)
    print("Rooms    :", assign_rooms(intervals))
    # Expected: minimal rooms = 3
    # Possible assignment: [0, 1, 0, 2, 1] (or similar valid assignment)

    # Edge cases
    print("\nTouching intervals (reuse allowed):")
    print("Intervals:", [[1, 3], [3, 5], [5, 7]])
    print("Rooms    :", assign_rooms([[1, 3], [3, 5], [5, 7]]))
    # Expected: [0, 0, 0]

    print("\nFully overlapping:")
    print("Intervals:", [[1, 10], [2, 3], [4, 5]])
    print("Rooms    :", assign_rooms([[1, 10], [2, 3], [4, 5]]))
    # Expected: [0, 1, 1]

    print("\nEmpty input:")
    print("Rooms    :", assign_rooms([]))
    # Expected: []