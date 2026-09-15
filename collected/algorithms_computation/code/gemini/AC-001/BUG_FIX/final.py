def find_max_simultaneous_meetings(intervals: list[tuple[int, int]]) -> tuple[int, list[int]]:
    """
    Finds the maximum number of simultaneously active meetings and the sorted times 
    at which that maximum begins.
    
    :param intervals: List of tuples representing half-open meeting intervals [start, end)
    :return: A tuple containing (max_active_meetings, sorted_peak_start_times)
    """
    if not intervals:
        return 0, []

    # 1. Generate start (+1) and end (-1) events
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))

    # 2. Sort events: time ascending; end events (-1) before start events (+1) at same timestamp
    events.sort(key=lambda x: (x[0], x[1]))

    # 3. Group deltas by timestamp to ensure atomic batch updates per timestamp
    aggregated_events = []
    for time, delta in events:
        if aggregated_events and aggregated_events[-1][0] == time:
            aggregated_events[-1] = (time, aggregated_events[-1][1] + delta)
        else:
            aggregated_events.append((time, delta))

    # 4. Sweep-line over aggregated timestamps
    max_active = 0
    current_active = 0
    peak_starts = []

    for time, net_delta in aggregated_events:
        prev_active = current_active
        current_active += net_delta

        if current_active > max_active:
            max_active = current_active
            peak_starts = [time]
        elif current_active == max_active and net_delta > 0 and prev_active < max_active:
            peak_starts.append(time)

    return max_active, peak_starts


if __name__ == "__main__":
    # Test case verifying deterministic behavior without duplicates:
    # Intervals with simultaneous starts and half-open boundary overlaps at time 4
    intervals = [
        (1, 4),  # ends at 4
        (4, 8),  # starts at 4 (end at 4 occurs before start at 4 -> active count at 4 is 2)
        (2, 6),  # active (2..6)
        (2, 7),  # active (2..7)
        (5, 7),  # starts at 5
    ]
    
    max_active, peak_starts = find_max_simultaneous_meetings(intervals)
    print(f"Max active meetings: {max_active}")
    print(f"Peak starts at: {peak_starts}")