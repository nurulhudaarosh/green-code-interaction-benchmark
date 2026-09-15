"""
Problem: Given half-open meeting intervals [start, end), find:
1. The maximum number of simultaneously active meetings.
2. The sorted times at which that maximum begins.

Key constraints:
- Intervals are half-open: [start, end) means active at t if start <= t < end.
- Times can be integers or floats (assumed comparable).
- Need deterministic output: times sorted ascending.

Algorithm:
- Sweep-line over events: for each interval, create (start, +1) and (end, -1).
- Sort events by time. For equal times, process end events (-1) before start events (+1)
  to handle half-open intervals correctly (meeting ending at t is not active at t).
- Sweep through events:
  - Apply all events at the same timestamp (ends first, then starts).
  - After applying events at time t, if current count > max_count, update max_count
    and reset max_start_times = [t].
  - If current count == max_count and t is not already the last recorded time, append t.
- Return max_count and sorted max_start_times.
"""

from typing import List, Tuple


def find_max_active_meetings(intervals: List[Tuple[float, float]]) -> Tuple[int, List[float]]:
    """
    Find maximum number of simultaneously active meetings and the times at which
    that maximum begins.

    Args:
        intervals: List of [start, end) intervals.

    Returns:
        Tuple of (max_count, sorted list of times at which max_count is achieved).
    """
    if not intervals:
        return 0, []

    # Build events: (time, delta)
    # delta = +1 for start, -1 for end
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))

    # Sort events:
    # Primary: time
    # Secondary: end events (-1) before start events (+1) for same time
    events.sort(key=lambda x: (x[0], x[1]))

    max_count = 0
    current_count = 0
    max_start_times = []

    i = 0
    n = len(events)

    while i < n:
        time = events[i][0]

        # Process all events at this timestamp: ends first, then starts
        # (already sorted by delta, so -1 before +1)
        while i < n and events[i][0] == time:
            current_count += events[i][1]
            i += 1

        # After processing all events at this time, check if we have a new max
        if current_count > max_count:
            max_count = current_count
            max_start_times = [time]
        elif current_count == max_count:
            # Avoid duplicate times (should not happen with sorted unique times,
            # but keep safe)
            if not max_start_times or max_start_times[-1] != time:
                max_start_times.append(time)

    return max_count, max_start_times


# Example usage and test cases
if __name__ == "__main__":
    # Test case 1: Basic overlap
    intervals1 = [(0, 5), (1, 6), (2, 7)]
    count1, times1 = find_max_active_meetings(intervals1)
    print(f"Intervals: {intervals1}")
    print(f"Max active: {count1}, at times: {times1}")
    # Expected: 3, [2]

    # Test case 2: Half-open handling (meeting ending at same time as another starting)
    intervals2 = [(0, 5), (5, 10), (2, 7)]
    count2, times2 = find_max_active_meetings(intervals2)
    print(f"\nIntervals: {intervals2}")
    print(f"Max active: {count2}, at times: {times2}")
    # Expected: 2, [2, 5] (at t=2 active: (0,5) and (2,7); at t=5 active: (2,7) and (5,10))

    # Test case 3: No overlap
    intervals3 = [(0, 1), (1, 2), (2, 3)]
    count3, times3 = find_max_active_meetings(intervals3)
    print(f"\nIntervals: {intervals3}")
    print(f"Max active: {count3}, at times: {times3}")
    # Expected: 1, [0, 1, 2]

    # Test case 4: Multiple max intervals
    intervals4 = [(0, 10), (1, 2), (2, 3), (3, 4)]
    count4, times4 = find_max_active_meetings(intervals4)
    print(f"\nIntervals: {intervals4}")
    print(f"Max active: {count4}, at times: {times4}")
    # Expected: 1, [0, 1, 2, 3] (since only one active at start of each interval)

    # Test case 5: Empty list
    intervals5 = []
    count5, times5 = find_max_active_meetings(intervals5)
    print(f"\nIntervals: {intervals5}")
    print(f"Max active: {count5}, at times: {times5}")
    # Expected: 0, []

    # Test case 6: All same start time
    intervals6 = [(0, 5), (0, 3), (0, 4)]
    count6, times6 = find_max_active_meetings(intervals6)
    print(f"\nIntervals: {intervals6}")
    print(f"Max active: {count6}, at times: {times6}")
    # Expected: 3, [0]

    # Test case 7: Complex with equal end/start
    intervals7 = [(1, 4), (2, 5), (4, 6), (3, 7)]
    count7, times7 = find_max_active_meetings(intervals7)
    print(f"\nIntervals: {intervals7}")
    print(f"Max active: {count7}, at times: {times7}")
    # Expected: 3, [3]