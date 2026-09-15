from typing import List, Tuple

def max_simultaneous_meetings(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Finds the maximum number of simultaneous meetings and the sorted timestamps
    at which that maximum concurrency begins.

    Args:
        intervals: List of tuples representing half-open intervals [start, end).

    Returns:
        A tuple containing:
            - max_active (int): Maximum number of concurrent meetings.
            - peak_starts (List[int]): Sorted list of timestamps where max concurrency starts.
    """
    if not intervals:
        return 0, []

    # Create events: (timestamp, type)
    # Type -1 for END (processed first), +1 for START (processed second)
    events = []
    for start, end in intervals:
        if start < end:  # Only process valid non-empty intervals
            events.append((start, 1))
            events.append((end, -1))

    # Sort events by time ascending; end events (-1) come before start events (+1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_active = 0
    current_active = 0
    peak_starts = []

    for time, event_type in events:
        previous_active = current_active
        current_active += event_type

        # Check if we hit a new maximum concurrency
        if current_active > max_active:
            max_active = current_active
            peak_starts = [time]
        # Check if we reached the existing maximum concurrency from a lower count
        elif current_active == max_active and previous_active < max_active:
            peak_starts.append(time)

    return max_active, peak_starts


if __name__ == "__main__":
    # Test Example 1: Standard overlapping intervals
    meetings1 = [(1, 5), (2, 6), (4, 8), (6, 9)]
    max_c1, starts1 = max_simultaneous_meetings(meetings1)
    print(f"Example 1 -> Max Active: {max_c1}, Peak Starts: {starts1}")
    # Output: Max Active: 3, Peak Starts: [4]

    # Test Example 2: End time matching start time [start, end)
    # At time 3, (1,3) ends before (3,5) starts -> active count drops to 0 then goes to 1
    meetings2 = [(1, 3), (3, 5), (2, 4)]
    max_c2, starts2 = max_simultaneous_meetings(meetings2)
    print(f"Example 2 -> Max Active: {max_c2}, Peak Starts: {starts2}")
    # Output: Max Active: 2, Peak Starts: [2, 3]