"""
Interval Conflict Analyzer

Problem:
Given half-open meeting intervals [start, end), find:
1. The maximum number of simultaneously active meetings.
2. The sorted times at which that maximum begins.

Key constraints:
- Intervals are half-open: [start, end).
- A meeting is active at time t when start <= t < end.
- End events at the same timestamp occur before start events.
- The output must be deterministic.
- Maximum-start times must be sorted.
- Only the Python standard library is used.

Algorithm:
Use a sweep-line over start/end events.
For each interval [start, end), create:
    (start, +1) for a start event
    (end, -1) for an end event

Sort events by (time, event_type), with end events (-1)
processed before start events (+1) at the same timestamp.

While sweeping:
- Apply each event.
- Track the current number of active meetings.
- When the active count becomes greater than the previous maximum,
  replace the maximum and record that timestamp.
- If the active count later returns to the same maximum, record
  that timestamp only when the maximum starts again.

Because intervals are half-open and end events are processed first,
a meeting ending at time t does not overlap with one starting at t.

Input format:
    The solution function accepts a list of (start, end) pairs.

Output:
    (maximum_active_meetings, sorted_maximum_start_times)

Example:
    intervals = [(1, 4), (2, 5), (4, 6)]

    Maximum active meetings = 2
    Maximum begins at time 2

    Result:
        (2, [2])

Note:
Zero-length intervals [t, t) are ignored because they contain no
active time.
"""


def interval_conflict_analyzer(intervals):
    """
    Return the maximum number of simultaneously active meetings and
    the sorted times at which that maximum begins.

    Parameters:
        intervals: iterable of (start, end) pairs

    Returns:
        tuple:
            (
                maximum_active_meetings,
                sorted list of times when the maximum begins
            )
    """

    events = []

    for start, end in intervals:
        # A half-open interval [start, end) with start == end
        # has no active duration.
        if start >= end:
            continue

        # End events use -1 and start events use +1.
        # Sorting by (time, delta) therefore processes ends first.
        events.append((start, 1))
        events.append((end, -1))

    if not events:
        return 0, []

    events.sort()

    active = 0
    maximum = 0
    maximum_starts = []

    i = 0

    while i < len(events):
        time = events[i][0]

        # Process all events at this timestamp.
        # Since events are sorted by delta, all -1 events come first.
        previous_active = active

        while i < len(events) and events[i][0] == time:
            active += events[i][1]
            i += 1

        # The maximum begins when, after processing this timestamp,
        # the active count becomes the new maximum.
        if active > maximum:
            maximum = active
            maximum_starts = [time]

        # If the active count reaches the existing maximum after
        # being below it, this timestamp is another beginning of
        # a maximum-active period.
        elif active == maximum and previous_active < maximum:
            maximum_starts.append(time)

    return maximum, sorted(maximum_starts)


if __name__ == "__main__":
    # Small deterministic example.
    intervals = [
        (1, 4),
        (2, 5),
        (4, 6),
    ]

    result = interval_conflict_analyzer(intervals)
    print(result)