Interval Conflict Analyzer

Problem:
Given half-open meeting intervals [start, end), determine:
1. The maximum number of simultaneously active meetings.
2. The sorted timestamps at which a maximum-concurrency period begins.

Expected behavior:
- [start, end) includes start but excludes end.
- End events at the same timestamp are processed before start events.
- A timestamp is included in max_start_times only when the maximum
  concurrency actually begins at that timestamp.
- If the maximum continues across a timestamp because one meeting ends
  and another starts, that timestamp is NOT added again.
- Results are deterministic.
- Empty input returns max_concurrent = 0 and an empty list.
- Invalid intervals where start >= end raise ValueError.
- Only the Python standard library is used.