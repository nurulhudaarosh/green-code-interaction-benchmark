def find_max_simultaneous_meetings(intervals: list[tuple[int, int]]) -> tuple[int, list[int]]:
    """
    Finds the maximum number of simultaneously active meetings and the sorted times 
    at which that maximum begins.
    
    :param intervals: List of tuples representing half-open meeting intervals [start, end)
    :return: A tuple containing (max_active_meetings, sorted_peak_start_times)
    """
    if not intervals:
        return 0, []

    events = []
    for start, end in intervals:
        events.append((start, 1))   # Meeting starts: increment count
        events.append((end, -1))    # Meeting ends: decrement count

    # Sort events primarily by timestamp ascending.
    # For equal timestamps, -1 (end event) comes before +1 (start event) to handle [start, end) properly.
    events.sort(key=lambda x: (x[0], x[1]))

    max_active = 0
    current_active = 0
    peak_starts = []

    for time, delta in events:
        prev_active = current_active
        current_active += delta

        if current_active > max_active:
            max_active = current_active
            peak_starts = [time]
        elif current_active == max_active and delta > 0 and prev_active < max_active:
            peak_starts.append(time)

    return max_active, peak_starts


if __name__ == "__main__":
    # Example test cases
    test_intervals = [
        (1, 4),
        (2, 6),
        (4, 8),
        (5, 7),
        (7, 9)
    ]
    
    max_meetings, peak_times = find_max_simultaneous_meetings(test_intervals)
    print(f"Maximum active meetings: {max_meetings}")
    print(f"Peak starts at: {peak_times}")