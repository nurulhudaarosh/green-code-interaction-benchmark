"""
Problem: Interval Room Assignment

Given a list of intervals, assign every interval to a room so that:
1. Overlapping intervals never use the same room.
2. A room can be reused when its previous interval ends at or before
   the next interval's start.
3. The total number of rooms is minimized.
4. Return the room ID assigned to every interval in its original order.

Key constraints / rules:
- Each interval is represented as (start, end).
- Intervals use the half-open interpretation [start, end).
- Therefore, an interval ending at time t can share a room with an
  interval starting at time t.
- Room IDs are deterministic and start from 0.
- If multiple rooms are available, reuse the room with the earliest
  availability; if tied, choose the smallest room ID.
- No randomness, network access, APIs, external services, or
  human interaction is used.
- Only the Python standard library is used.

Required output:
Return:
    {
        "room_count": minimum number of rooms required,
        "assignments": room ID for each interval in original input order
    }

Algorithm:
1. Sort intervals by (start time, end time, original index).
2. Maintain a min-heap of currently occupied rooms using:
       (end_time, room_id)
   so the room that becomes available earliest is considered first.
3. Before assigning an interval, release every room whose end time
   is <= the interval's start time.
4. If a released room exists, reuse the one with the smallest
   room ID. Otherwise, create a new room.
5. Store the assigned room ID at the interval's original index.
6. The number of rooms created is the minimum possible because a new
   room is required exactly when every existing room overlaps the
   current interval.

Implementation:
- Standard library only.
- Time complexity: O(n log n).
- Space complexity: O(n).
"""

from heapq import heappush, heappop
from typing import List, Tuple, Dict, Any


def assign_rooms(intervals: List[Tuple[int, int]]) -> Dict[str, Any]:
    """
    Assign every interval to a minimum number of rooms.

    Args:
        intervals:
            A list of (start, end) intervals.

    Returns:
        A dictionary containing:
            room_count: minimum number of rooms required
            assignments: room ID for each original interval
    """

    n = len(intervals)

    if n == 0:
        return {
            "room_count": 0,
            "assignments": []
        }

    # Sort by start time, then end time, then original index.
    ordered = sorted(
        (
            (start, end, index)
            for index, (start, end) in enumerate(intervals)
        ),
        key=lambda item: (item[0], item[1], item[2])
    )

    # Occupied rooms:
    # (end_time, room_id)
    occupied = []

    # Rooms that have become available.
    available = []

    assignments = [-1] * n
    next_room_id = 0

    for start, end, original_index in ordered:
        # Move every room that is available by this interval's start
        # time into the reusable-room heap.
        while occupied and occupied[0][0] <= start:
            end_time, room_id = heappop(occupied)
            heappush(available, room_id)

        # Reuse the smallest available room ID if possible.
        if available:
            room_id = heappop(available)
        else:
            room_id = next_room_id
            next_room_id += 1

        assignments[original_index] = room_id

        # This room is occupied until 'end'.
        heappush(occupied, (end, room_id))

    return {
        "room_count": next_room_id,
        "assignments": assignments
    }


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def _validate_assignment(
    intervals: List[Tuple[int, int]],
    result: Dict[str, Any]
) -> None:
    """Validate the returned room assignment."""

    room_count = result["room_count"]
    assignments = result["assignments"]

    assert len(assignments) == len(intervals)

    if intervals:
        assert room_count >= 1
        assert all(0 <= room < room_count for room in assignments)
    else:
        assert room_count == 0
        return

    # Intervals assigned to the same room must not overlap.
    by_room = {}

    for i, room in enumerate(assignments):
        by_room.setdefault(room, []).append(i)

    for indices in by_room.values():
        indices.sort(key=lambda i: (intervals[i][0], intervals[i][1], i))

        for a, b in zip(indices, indices[1:]):
            first_start, first_end = intervals[a]
            second_start, second_end = intervals[b]

            assert first_end <= second_start, (
                "Overlapping intervals were assigned to the same room."
            )

    # Verify that the number of rooms is actually the maximum overlap.
    events = []

    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))

    # At the same timestamp, end events happen before start events.
    events.sort(key=lambda event: (event[0], event[1]))

    active = 0
    maximum_overlap = 0

    for _, delta in events:
        active += delta
        maximum_overlap = max(maximum_overlap, active)

    assert room_count == maximum_overlap


def run_tests() -> None:
    # Test 1: No overlap, so one room is enough.
    intervals = [
        (1, 3),
        (3, 5),
        (5, 8),
    ]

    result = assign_rooms(intervals)

    assert result == {
        "room_count": 1,
        "assignments": [0, 0, 0],
    }
    _validate_assignment(intervals, result)

    # Test 2: Three overlapping intervals require three rooms.
    intervals = [
        (1, 5),
        (2, 6),
        (3, 4),
    ]

    result = assign_rooms(intervals)

    assert result["room_count"] == 3
    _validate_assignment(intervals, result)

    # Test 3: Input order differs from processing order.
    intervals = [
        (5, 7),
        (1, 3),
        (2, 4),
        (3, 5),
    ]

    result = assign_rooms(intervals)

    assert result["room_count"] == 2
    assert result["assignments"] == [0, 0, 1, 0]
    _validate_assignment(intervals, result)

    # Test 4: End time equal to start time means the room can be reused.
    intervals = [
        (1, 2),
        (2, 3),
        (2, 4),
    ]

    result = assign_rooms(intervals)

    assert result["room_count"] == 2
    _validate_assignment(intervals, result)

    # Test 5: Same start time. Deterministic room allocation.
    intervals = [
        (1, 4),
        (1, 3),
        (1, 2),
    ]

    result = assign_rooms(intervals)

    assert result["room_count"] == 3
    assert result["assignments"] == [2, 1, 0]
    _validate_assignment(intervals, result)

    # Test 6: Empty input.
    intervals = []

    result = assign_rooms(intervals)

    assert result == {
        "room_count": 0,
        "assignments": [],
    }
    _validate_assignment(intervals, result)

    # Test 7: Single interval.
    intervals = [(10, 20)]

    result = assign_rooms(intervals)

    assert result == {
        "room_count": 1,
        "assignments": [0],
    }
    _validate_assignment(intervals, result)

    # Test 8: All intervals overlap.
    intervals = [
        (0, 10),
        (1, 9),
        (2, 8),
        (3, 7),
    ]

    result = assign_rooms(intervals)

    assert result["room_count"] == 4
    _validate_assignment(intervals, result)

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()