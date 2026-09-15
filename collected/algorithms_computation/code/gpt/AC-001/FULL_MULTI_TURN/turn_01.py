Interval Conflict Analyzer

Problem:
Given half-open meeting intervals [start, end), find:
1. The maximum number of simultaneously active meetings.
2. The sorted timestamps at which this maximum concurrency begins.

Key constraints:
- Intervals are half-open: [start, end).
- A meeting is active at time t when start <= t < end.
- End events at the same timestamp are processed before start events.
- Results must be deterministic.
- No randomness, network access, APIs, external services, or human interaction.
- Standard library only.

Algorithm:
Use a sweep-line over start/end events.
For every interval:
    - Create a start event at start.
    - Create an end event at end.
Sort events by:
    1. timestamp
    2. event type, with end events before start events

Sweep through the events while tracking the active-meeting count.
Whenever the count becomes larger than the previous maximum, record
that timestamp as the beginning of a new maximum-concurrency period.

Because intervals are half-open and end events are processed before
start events at the same timestamp, a meeting ending at t does not
overlap with a meeting starting at t.

Required output:
A dictionary containing:
    {
        "max_concurrent": maximum number of simultaneously active meetings,
        "max_start_times": sorted timestamps at which that maximum begins
    }

For empty input, the maximum concurrency is 0 and the list of start
times is empty.



def analyze_intervals(intervals):