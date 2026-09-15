from typing import List, Tuple

def max_simultaneous_meetings(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Finds the peak number of simultaneous meetings and the sorted start times
    where that peak begins for half-open intervals [start, end).
    
    :param intervals: List of tuples/lists representing [start, end)
    :return: A tuple containing (max_active_count, sorted_start_timestamps)
    """
    if not intervals:
        return 0, []

    # 1. Generate events: (timestamp, delta)
    # delta is -1 for end, +1 for start.
    # Sorting (-1 before +1) ensures ends are processed before starts at the same timestamp.
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))

    # 2. Sort events by timestamp ascending, then by delta ascending (-1 before 1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_active = 0
    current_active = 0
    max_starts = []

    # 3. Sweep line
    for time, delta in events:
        previous_active = current_active
        current_active += delta

        # If we hit a new maximum
        if current_active > max_active:
            max_active = current_active
            max_starts = [time]
        # If we reach the existing maximum via a start event
        elif current_active == max_active and delta == 1:
            # Ensure we don't add duplicate timestamps if multiple start events occur at 'time'
            if not max_starts or max_starts[-1] != time:
                max_starts.append(time)

    return max_active, max_starts


if __name__ == "__main__":
    # Test cases
    test_intervals = [
        (1, 4),
        (2, 5),
        (4, 7),  # (1,4) ends at 4, (4,7) starts at 4 -> No overlap at t=4
        (3, 8),
        (5, 9)
    ]

    max_count, start_times = max_simultaneous_meetings(test_intervals)
    print(f"Maximum simultaneous meetings: {max_count}")
    print(f"Starts at timestamps: {start_times}")