"""
Minimum Room Assignment — with optional operation_summary

Original problem:
Assign every interval to a room so that overlapping intervals never share
a room. A room may be reused when its previous interval ends at or before
the next interval's start. The algorithm must minimize the number of rooms
and return the room ID assigned to every original interval.

Original required output:
- A list of room IDs.
- result[i] is the room assigned to intervals[i].
- Every interval receives exactly one room.
- Overlapping intervals never use the same room.
- The total number of rooms is minimum.
- Room IDs are deterministic and start from 0.
- Intervals are treated as half-open: [start, end).
- Deterministic tie handling:
    1. Sort intervals by (start, end, original_index).
    2. When several rooms are available, reuse the smallest room ID.

New optional feature:
When include_operation_summary=True, return a dictionary containing:
    {
        "room_assignments": [...],
        "operation_summary": {
            "intervals_processed": n,
            "rooms_created": ...,
            "rooms_reused": ...,
            "rooms_released": ...,
            "availability_checks": ...,
            "total_major_operations": ...
        }
    }

The summary is deterministic:
- intervals_processed: number of input intervals.
- rooms_created: number of times a new room was necessary.
- rooms_reused: number of intervals assigned to an already-created room.
- rooms_released: number of occupied-room entries removed from the heap.
- availability_checks: number of heap-top availability checks made while
  releasing rooms.
- total_major_operations: the sum of the above five operation counts.

When include_operation_summary=False (the default), the original output
format is preserved exactly: only the list of room IDs is returned.

Algorithm:
1. Sort intervals by (start, end, original_index).
2. Use a min-heap of occupied rooms keyed by (end_time, room_id).
3. Before assigning an interval, release rooms whose end_time <= start.
4. Keep released room IDs in a second min-heap.
5. Reuse the smallest available room ID.
6. If no room is available, create a new room.
7. Store each assignment using its original input index.

Complexity:
- Sorting: O(n log n)
- Heap operations: O(n log n)
- Space: O(n)

Only Python's standard library is used.
No network, APIs, external services, randomness, or human interaction.
"""

from heapq import heappop, heappush


def assign_rooms(intervals, include_operation_summary=False):
    """
    Assign every interval to a minimum number of rooms.

    Parameters:
        intervals: list of (start, end) pairs
        include_operation_summary: if True, return the assignments together
            with a deterministic operation summary.

    Returns:
        If include_operation_summary is False:
            list[int]

        If include_operation_summary is True:
            {
                "room_assignments": list[int],
                "operation_summary": dict
            }
    """
    n = len(intervals)

    if n == 0:
        result = []

        if not include_operation_summary:
            return result

        summary = {
            "intervals_processed": 0,
            "rooms_created": 0,
            "rooms_reused": 0,
            "rooms_released": 0,
            "availability_checks": 0,
            "total_major_operations": 0,
        }

        return {
            "room_assignments": result,
            "operation_summary": summary,
        }

    ordered = [
        (start, end, index)
        for index, (start, end) in enumerate(intervals)
    ]

    ordered.sort(key=lambda item: (item[0], item[1], item[2]))

    # (end_time, room_id)
    occupied = []

    # Free room IDs.
    available = []

    result = [-1] * n
    next_room_id = 0

    # Operation counters.
    rooms_created = 0
    rooms_reused = 0
    rooms_released = 0
    availability_checks = 0

    for start, end, original_index in ordered:

        # Each loop iteration represents one availability check.
        while occupied:
            availability_checks += 1

            if occupied[0][0] > start:
                break

            end_time, room_id = heappop(occupied)
            heappush(available, room_id)
            rooms_released += 1

        if available:
            room_id = heappop(available)
            rooms_reused += 1
        else:
            room_id = next_room_id
            next_room_id += 1
            rooms_created += 1

        result[original_index] = room_id
        heappush(occupied, (end, room_id))

    if not include_operation_summary:
        return result

    total_major_operations = (
        n
        + rooms_created
        + rooms_reused
        + rooms_released
        + availability_checks
    )

    summary = {
        "intervals_processed": n,
        "rooms_created": rooms_created,
        "rooms_reused": rooms_reused,
        "rooms_released": rooms_released,
        "availability_checks": availability_checks,
        "total_major_operations": total_major_operations,
    }

    return {
        "room_assignments": result,
        "operation_summary": summary,
    }


# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

def test_original_output_is_unchanged_by_default():
    intervals = [
        (1, 4),
        (2, 5),
        (5, 7),
    ]

    assert assign_rooms(intervals) == [0, 1, 0]


def test_operation_summary():
    intervals = [
        (1, 4),  # creates room 0
        (2, 5),  # creates room 1
        (5, 7),  # releases both, reuses room 0
    ]

    result = assign_rooms(
        intervals,
        include_operation_summary=True
    )

    assert result["room_assignments"] == [0, 1, 0]

    assert result["operation_summary"] == {
        "intervals_processed": 3,
        "rooms_created": 2,
        "rooms_reused": 1,
        "rooms_released": 2,
        "availability_checks": 4,
        "total_major_operations": 12,
    }


def test_empty_input():
    assert assign_rooms([]) == []

    result = assign_rooms(
        [],
        include_operation_summary=True
    )

    assert result == {
        "room_assignments": [],
        "operation_summary": {
            "intervals_processed": 0,
            "rooms_created": 0,
            "rooms_reused": 0,
            "rooms_released": 0,
            "availability_checks": 0,
            "total_major_operations": 0,
        },
    }


def test_end_at_start_reuses_room():
    intervals = [
        (1, 3),
        (3, 5),
        (5, 7),
    ]

    result = assign_rooms(
        intervals,
        include_operation_summary=True
    )

    assert result["room_assignments"] == [0, 0, 0]
    assert result["operation_summary"]["rooms_created"] == 1
    assert result["operation_summary"]["rooms_reused"] == 2
    assert result["operation_summary"]["rooms_released"] == 2


def test_overlapping_intervals_require_multiple_rooms():
    intervals = [
        (1, 4),
        (2, 5),
        (3, 6),
    ]

    result = assign_rooms(
        intervals,
        include_operation_summary=True
    )

    assert result["room_assignments"] == [0, 1, 2]
    assert result["operation_summary"]["rooms_created"] == 3
    assert result["operation_summary"]["rooms_reused"] == 0


def test_deterministic_smallest_available_room():
    intervals = [
        (1, 2),  # room 0
        (1, 3),  # room 1
        (1, 4),  # room 2
        (4, 5),  # all rooms free -> room 0
    ]

    result = assign_rooms(
        intervals,
        include_operation_summary=True
    )

    assert result["room_assignments"] == [0, 1, 2, 0]


def test_original_indices_are_preserved():
    intervals = [
        (5, 7),
        (1, 3),
        (3, 5),
    ]

    result = assign_rooms(
        intervals,
        include_operation_summary=True
    )

    assert result["room_assignments"] == [0, 0, 0]


def test_same_start_deterministic():
    intervals = [
        (2, 5),
        (2, 4),
        (2, 3),
    ]

    result = assign_rooms(
        intervals,
        include_operation_summary=True
    )

    # Processing order:
    # (2,3) -> room 0
    # (2,4) -> room 1
    # (2,5) -> room 2
    #
    # Mapped back to original order:
    assert result["room_assignments"] == [2, 1, 0]


if __name__ == "__main__":
    test_original_output_is_unchanged_by_default()
    test_operation_summary()
    test_empty_input()
    test_end_at_start_reuses_room()
    test_overlapping_intervals_require_multiple_rooms()
    test_deterministic_smallest_available_room()
    test_original_indices_are_preserved()
    test_same_start_deterministic()

    print("All tests passed.")