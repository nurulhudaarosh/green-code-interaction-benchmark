"""
Minimum Room Assignment

Problem:
Assign every interval to a room so that overlapping intervals never share
the same room. A room may be reused when its previous interval ends at or
before the next interval starts. The number of rooms must be minimized, and
the returned room IDs must be deterministic.

Expected behavior:
- Every input interval receives exactly one room ID.
- Overlapping intervals must have different room IDs.
- If a room becomes available at time t, it may be reused by an interval
  starting at time t.
- The minimum possible number of rooms must be used.
- Intervals are processed in increasing start-time order.
- When multiple rooms are available, deterministic tie handling selects
  the room with the smallest room ID among those with the earliest
  availability.
- The returned assignment remains in the original input order.
- Invalid intervals with start > end raise ValueError.
- Empty input returns zero rooms and an empty assignment list.

Bug demonstration:
A common defective implementation keeps available rooms in an ordinary
list and chooses the first room it finds instead of using a min-heap keyed
by `(availability_time, room_id)`.

Example:
    intervals = [
        (0, 5),   # original interval 0
        (0, 10),  # original interval 1
        (5, 6),   # original interval 2
    ]

After the first two intervals:
    room 0 is available at 5
    room 1 is available at 10

At time 5, interval 2 can reuse room 0.

A defective implementation that happens to inspect room 1 first may assign
interval 2 to room 1 even though room 0 is the earliest available room.
That still uses two rooms, but it violates the required deterministic
tie-handling rule.

The correction is to maintain:
    (availability_time, room_id)
in a min-heap. Therefore the earliest available room is always selected,
and equal availability times are resolved by the smaller room ID.

Algorithm:
1. Sort intervals by `(start, end, original_index)`.
2. Maintain a min-heap containing `(availability_time, room_id)`.
3. For each interval, if the earliest room has availability <= start,
   reuse that room.
4. Otherwise, create a new room.
5. Push the selected room back into the heap with its new availability
   equal to the interval's end.
6. Store each assignment at its original index.

Complexity:
- Sorting: O(n log n)
- Heap operations: O(n log n)
- Total: O(n log n)
- Space: O(n)

The implementation below fixes only the room-selection/tie-handling issue
and preserves the original requirements.
"""

from heapq import heappop, heappush
from typing import List, Sequence, Tuple


def minimum_room_assignment(
    intervals: Sequence[Tuple[int, int]]
) -> Tuple[int, List[int]]:
    """
    Return the minimum number of rooms and the room ID assigned to each
    original interval.

    Intervals use half-open semantics [start, end).
    """

    n = len(intervals)

    if n == 0:
        return 0, []

    # Validate input without changing unrelated requirements.
    for start, end in intervals:
        if start > end:
            raise ValueError("Interval start cannot be greater than its end.")

    # Deterministic processing:
    # primary key   -> start time
    # secondary key -> end time
    # final key     -> original index
    ordered = sorted(
        (start, end, index)
        for index, (start, end) in enumerate(intervals)
    )

    # Min-heap keyed first by room availability and then by room ID.
    #
    # This is the important correction:
    # the heap guarantees that the earliest available room is selected,
    # while room_id provides deterministic tie handling.
    room_heap: List[Tuple[int, int]] = []

    room_ids = [-1] * n
    next_room_id = 0

    for start, end, original_index in ordered:
        # Reuse the earliest available room whenever possible.
        if room_heap and room_heap[0][0] <= start:
            availability, room_id = heappop(room_heap)
        else:
            # No existing room is available, so a new room is necessary.
            room_id = next_room_id
            next_room_id += 1

        room_ids[original_index] = room_id

        # This room becomes available when the current interval ends.
        heappush(room_heap, (end, room_id))

    return next_room_id, room_ids


def run_tests() -> None:
    # ------------------------------------------------------------
    # 1. Small example demonstrating deterministic room reuse.
    # ------------------------------------------------------------
    intervals = [
        (0, 5),   # room 0
        (0, 10),  # room 1
        (5, 6),   # must reuse room 0
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 2
    assert assignments == [0, 1, 0]

    # ------------------------------------------------------------
    # 2. Non-overlapping intervals reuse one room.
    # ------------------------------------------------------------
    intervals = [
        (1, 3),
        (3, 5),
        (5, 8),
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 1
    assert assignments == [0, 0, 0]

    # ------------------------------------------------------------
    # 3. Fully overlapping intervals require three rooms.
    # ------------------------------------------------------------
    intervals = [
        (1, 5),
        (2, 6),
        (3, 7),
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 3
    assert assignments == [0, 1, 2]

    # ------------------------------------------------------------
    # 4. End at start is NOT overlapping.
    # ------------------------------------------------------------
    intervals = [
        (1, 2),
        (2, 3),
        (3, 4),
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 1
    assert assignments == [0, 0, 0]

    # ------------------------------------------------------------
    # 5. Multiple rooms become available at the same time.
    #    Smaller room ID must win deterministically.
    # ------------------------------------------------------------
    intervals = [
        (0, 5),   # room 0
        (0, 5),   # room 1
        (5, 6),   # must choose room 0
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 2
    assert assignments == [0, 1, 0]

    # ------------------------------------------------------------
    # 6. Original input order must be preserved.
    # ------------------------------------------------------------
    intervals = [
        (5, 6),   # original index 0
        (1, 5),   # original index 1
        (0, 3),   # original index 2
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 2
    assert len(assignments) == 3

    # Verify the actual assignment is valid.
    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            s1, e1 = intervals[i]
            s2, e2 = intervals[j]

            overlap = max(s1, s2) < min(e1, e2)

            if overlap:
                assert assignments[i] != assignments[j]

    # ------------------------------------------------------------
    # 7. Equal start times are deterministic.
    # ------------------------------------------------------------
    intervals = [
        (1, 4),
        (1, 4),
        (1, 4),
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 3
    assert assignments == [0, 1, 2]

    # ------------------------------------------------------------
    # 8. Zero-length intervals.
    # ------------------------------------------------------------
    intervals = [
        (2, 2),
        (2, 2),
        (2, 3),
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 1
    assert assignments == [0, 0, 0]

    # ------------------------------------------------------------
    # 9. Empty input.
    # ------------------------------------------------------------
    rooms, assignments = minimum_room_assignment([])

    assert rooms == 0
    assert assignments == []

    # ------------------------------------------------------------
    # 10. Negative times.
    # ------------------------------------------------------------
    intervals = [
        (-5, -2),
        (-4, 0),
        (-2, 3),
    ]

    rooms, assignments = minimum_room_assignment(intervals)

    assert rooms == 2
    assert len(assignments) == 3

    # ------------------------------------------------------------
    # 11. Invalid interval.
    # ------------------------------------------------------------
    try:
        minimum_room_assignment([(5, 2)])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()