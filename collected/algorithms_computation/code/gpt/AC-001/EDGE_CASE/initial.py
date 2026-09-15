Interval Conflict Analyzer

Problem:
Given half-open meeting intervals [start, end), find:
1. The maximum number of simultaneously active meetings.
2. The sorted times at which that maximum begins.

Key constraints:
- Intervals are half-open: [start, end).
- A meeting is active at time t when start <= t < end.
- Meetings with end == start at the same timestamp do not overlap.
- End events at the same timestamp are processed before start events.
- Results must be deterministic.
- Only the Python standard library is used.

Algorithm:
Use a sweep-line over start/end events.
For each interval:
    - Add a start event at start.
    - Add an end event at end.

Events are sorted by:
    1. timestamp
    2. event type, with end events before start events

While sweeping:
- Process all events at each timestamp.
- Apply end events first, then start events.
- If the active count becomes larger than the previous maximum,
  record that timestamp as the beginning of a new maximum.
- If the active count returns to the same maximum later, record
  that timestamp only when the maximum begins again.

Output:
{
    "max_concurrent": int,
    "peak_times": list
}

For empty input, the result is:
{
    "max_concurrent": 0,
    "peak_times": []
}