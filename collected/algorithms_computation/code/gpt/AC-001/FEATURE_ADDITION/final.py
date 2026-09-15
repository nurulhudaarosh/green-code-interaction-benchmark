Interval Conflict Analyzer

Original Problem:
Given a collection of half-open meeting intervals [start, end), find:
1. The maximum number of simultaneously active meetings.
2. The sorted times at which that maximum begins.

Original Requirements:
- Intervals are half-open: [start, end).
- A meeting is active at time t when start <= t < end.
- End events at the same timestamp occur before start events.
- Results must be deterministic.
- Maximum-start times must be sorted.
- Use a sweep-line over start/end events.
- Use only the Python standard library.
- Do not use network access, APIs, external services, randomness, or
  human interaction.
- Zero-length intervals [t, t) contain no active time and are ignored.

Existing Output:
    (
        maximum_active_meetings,
        sorted_maximum_start_times
    )

New Feature:
When operation_summary is requested, return an additional
`operation_summary` field containing a deterministic summary of the
major computational decisions/operations made by the algorithm.

The summary reports:
- event_operations: number of individual start/end events processed
- timestamp_decisions: number of distinct timestamps examined
- maximum_updates: number of times a new maximum was established

The feature is disabled by default so the original return format and
requirements remain unchanged.

New Output when requested:
    (
        maximum_active_meetings,
        sorted_maximum_start_times,
        operation_summary
    )

Example:
    intervals = [(1, 4), (2, 5), (4, 6)]

    Without summary:
        (2, [2])

    With summary:
        (
            2,
            [2],
            {
                "event_operations": 6,
                "timestamp_decisions": 5,
                "maximum_updates": 2
            }
        )


Algorithm:
Use a sweep-line over start/end events.

For every non-empty interval [start, end):
    - Add (start, +1) for a start event.
    - Add (end, -1) for an end event.

Sort events by (time, delta). Since -1 sorts before +1,
end events at the same timestamp occur before start events.

At each distinct timestamp:
    1. Process all events at that timestamp.
    2. Update the number of active meetings.
    3. If the new active count exceeds the previous maximum,
       record that timestamp as a new maximum beginning.
    4. If the active count returns to the existing maximum after
       being below it, record that timestamp as another beginning.

Complexity:
- Let n be the number of intervals.
- There are at most 2n events.
- Sorting takes O(n log n).
- The sweep takes O(n).
- Overall: O(n log n) time and O(n) space.