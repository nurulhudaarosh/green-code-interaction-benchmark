Interval Conflict Analyzer

Original problem:
Given half-open meeting intervals [start, end), determine:
1. The maximum number of simultaneously active meetings.
2. The sorted timestamps at which a maximum-concurrency period begins.

Original requirements:
- Intervals are half-open: [start, end).
- End events at the same timestamp occur before start events.
- Results are deterministic.
- Invalid intervals where start >= end raise ValueError.
- Empty input returns:
      {
          "max_concurrent": 0,
          "max_start_times": []
      }
- Use a sweep-line over start/end events.
- Standard library only.
- No randomness, network access, APIs, external services, or
  human interaction.

New optional feature:
- If include_operation_summary=True, add:
      "operation_summary": {
          "major_operations": <integer>
      }
- major_operations is the deterministic number of sweep-line events
  processed.
- If include_operation_summary is False or omitted, the original
  output format is preserved exactly.