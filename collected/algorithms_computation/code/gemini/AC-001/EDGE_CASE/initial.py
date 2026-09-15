"""
Sweep-Line Algorithm for Finding Maximum Simultaneous Meetings.
"""

from typing import List, Tuple


def max_simultaneous_meetings(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Finds the maximum number of simultaneous active meetings and the sorted 
    timestamps where that maximum level of overlap begins.

    Args:
        intervals: List of half-open intervals [start, end).

    Returns:
        A tuple containing:
            - max_active (int): Maximum count of concurrent meetings.
            - start_times (List[int]): Sorted timestamps where max active count begins.
    """
    if not intervals:
        return 0, []

    # Step 1: Create events.
    # Event format: (timestamp, event_type)
    # event_type is -1 for END, +1 for START.
    # Since -1 < 1, Python's default sorting processes END events before START events at the same timestamp.
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))

    # Step 2: Sort events by timestamp, breaking ties with event_type (-1 before +1)
    events.sort(key=lambda x: (x[0], x[1]))

    current_active = 0
    max_active = 0
    max_start_times = []

    # Step 3: Sweep line through sorted events
    for time, event_type in events:
        prev_active = current_active
        current_active += event_type

        # Check if we hit a new maximum peak
        if current_active > max_active:
            max_active = current_active
            max_start_times = [time]  # Reset list with the new max start time
        # Check if we reached an existing maximum peak again
        elif current_active == max_active and prev_active == max_active - 1:
            max_start_times.append(time)

    return max_active, max_start_times


if __name__ == "__main__":
    # Example Test Case
    # Intervals: [1, 5), [2, 6), [4, 8), [6, 9), [6, 10)
    test_intervals = [
        (1, 5),
        (2, 6),
        (4, 8),
        (6, 9),
        (6, 10),
    ]

    max_count, peak_starts = max_simultaneous_meetings(test_intervals)
    print(f"Intervals: {test_intervals}")
    print(f"Maximum simultaneous meetings: {max_count}")
    print(f"Sorted timestamps where maximum begins: {peak_starts}")