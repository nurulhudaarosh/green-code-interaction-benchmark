Interval Conflict Analyzer

Problem:
Given half-open meeting intervals [start, end), determine:
1. The maximum number of simultaneously active meetings.
2. The sorted timestamps at which a maximum-concurrency period begins.

Optional feature:
When include_operation_summary=True, also return:
    "operation_summary": {
        "major_operations": <number of sweep-line events processed>
    }

Rules:
- Intervals are half-open: [start, end).
- A meeting is active at t when start <= t < end.
- End events at the same timestamp occur before start events.
- A maximum start time is recorded only when a new maximum begins.
- Results are deterministic.
- Invalid intervals where start >= end raise ValueError.
- Empty input is valid.
- Standard library only.