def max_simultaneous_meetings(intervals: list[tuple[int, int]]) -> tuple[int, list[int]]:
    """
    Finds the maximum number of simultaneously active half-open meeting intervals [start, end)
    and the sorted timestamps at which that maximum level of concurrency begins.

    Args:
        intervals: List of tuples/lists representing [start, end) meeting times.

    Returns:
        A tuple containing:
            - int: Maximum number of simultaneous meetings.
            - list[int]: Sorted timestamps where maximum concurrency is first reached.
    """
    if not intervals:
        return 0, []

    # End events (-1) come before start events (+1) at the same timestamp
    # because intervals are half-open [start, end).
    events = []
    for start, end in intervals:
        events.append((start, 1))   # Start meeting
        events.append((end, -1))   # End meeting

    # Sort primarily by timestamp ascending, secondarily by change (-1 before 1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_active = 0
    current_active = 0
    peak_start_times = []

    for time, change in events:
        previous_active = current_active
        current_active += change

        # Peak reached via a start event
        if change > 0:
            if current_active > max_active:
                max_active = current_active
                peak_start_times = [time]
            elif current_active == max_active and previous_active < max_active:
                if not peak_start_times or peak_start_times[-1] != time:
                    peak_start_times.append(time)

    return max_active, peak_start_times


if __name__ == "__main__":
    # Test cases
    sample_intervals = [
        (1, 4),
        (2, 5),
        (4, 6),
        (5, 8),
        (5, 7),
        (7, 9)
    ]
    
    max_count, peak_times = max_simultaneous_meetings(sample_intervals)
    print(f"Max Simultaneous Meetings: {max_count}")
    print(f"Peak Start Times: {peak_times}")