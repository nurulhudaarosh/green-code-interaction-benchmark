"""
Problem: Given a list of half-open meeting intervals [start, end),
find the maximum number of simultaneously active meetings and the sorted
times at which that maximum begins.

Key constraints:
- Intervals are half-open: [start, end)
- A meeting is active at time t if start <= t < end
- At a given timestamp, end events occur before start events
- Need to output: maximum count and sorted list of start times where
  this maximum is achieved

Algorithm: Sweep-line over events
1. Create events: (time, type) where type=0 for end, type=1 for start
   (end before start ensures proper handling at boundaries)
2. Sort events by time, then by type
3. Sweep through events, maintaining current active count
4. Track maximum count and the start times when maximum is reached
5. For each start event, if count after adding equals max, record the time

Time complexity: O(n log n) due to sorting
Space complexity: O(n)
"""

from typing import List, Tuple


def find_max_active_meetings(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Find the maximum number of simultaneously active meetings and the sorted
    times at which that maximum begins.

    Args:
        intervals: List of [start, end) meeting intervals

    Returns:
        Tuple of (max_count, list_of_start_times)
        Returns (0, []) for empty input
    """
    if not intervals:
        return 0, []

    # Create events: (time, type)
    # type: 0 for end, 1 for start (end before start at same timestamp)
    events = []
    for start, end in intervals:
        events.append((start, 1))  # start event
        events.append((end, 0))    # end event

    # Sort by time, then by type (end before start)
    events.sort(key=lambda x: (x[0], x[1]))

    max_count = 0
    current_count = 0
    result_times = []

    i = 0
    while i < len(events):
        time = events[i][0]

        # Process all end events at this timestamp first
        while i < len(events) and events[i][0] == time and events[i][1] == 0:
            current_count -= 1
            i += 1

        # Then process all start events at this timestamp
        # Count how many start events at this time
        start_count = 0
        while i < len(events) and events[i][0] == time and events[i][1] == 1:
            current_count += 1
            start_count += 1
            i += 1

        # After processing events at this timestamp, check if we reached max
        if current_count > max_count:
            max_count = current_count
            # This time is a new maximum start time
            result_times = [time]
        elif current_count == max_count and start_count > 0:
            # If we reached the same maximum with a start event at this time
            # Only add if this time isn't already the last recorded (avoid duplicates)
            if not result_times or result_times[-1] != time:
                result_times.append(time)

    return max_count, result_times


def main():
    """Test the function with sample inputs."""
    # Test case 1: Basic overlapping intervals
    intervals1 = [(0, 5), (1, 6), (2, 7), (3, 8)]
    count1, times1 = find_max_active_meetings(intervals1)
    print(f"Intervals: {intervals1}")
    print(f"Max active: {count1}, at times: {times1}")
    print()

    # Test case 2: Intervals with gaps
    intervals2 = [(0, 2), (1, 3), (4, 6), (5, 7)]
    count2, times2 = find_max_active_meetings(intervals2)
    print(f"Intervals: {intervals2}")
    print(f"Max active: {count2}, at times: {times2}")
    print()

    # Test case 3: Touch at endpoints (half-open intervals)
    intervals3 = [(0, 5), (5, 10), (10, 15)]
    count3, times3 = find_max_active_meetings(intervals3)
    print(f"Intervals: {intervals3}")
    print(f"Max active: {count3}, at times: {times3}")
    print()

    # Test case 4: Multiple meetings starting at same time
    intervals4 = [(0, 5), (0, 6), (0, 7), (1, 2)]
    count4, times4 = find_max_active_meetings(intervals4)
    print(f"Intervals: {intervals4}")
    print(f"Max active: {count4}, at times: {times4}")
    print()

    # Test case 5: Empty input
    intervals5 = []
    count5, times5 = find_max_active_meetings(intervals5)
    print(f"Intervals: {intervals5}")
    print(f"Max active: {count5}, at times: {times5}")
    print()

    # Test case 6: End events before start events at same timestamp
    intervals6 = [(0, 2), (2, 4), (2, 3)]
    count6, times6 = find_max_active_meetings(intervals6)
    print(f"Intervals: {intervals6}")
    print(f"Max active: {count6}, at times: {times6}")
    print()

    # Test case 7: All meetings non-overlapping
    intervals7 = [(0, 1), (2, 3), (4, 5)]
    count7, times7 = find_max_active_meetings(intervals7)
    print(f"Intervals: {intervals7}")
    print(f"Max active: {count7}, at times: {times7}")


if __name__ == "__main__":
    main()