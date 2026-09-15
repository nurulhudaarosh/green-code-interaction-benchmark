Interval Conflict Analyzer

Problem:
Given half-open meeting intervals [start, end), find:
1. The maximum number of simultaneously active meetings.
2. The sorted times at which that maximum begins.

Half-open interval rule:
A meeting [start, end) is active at time t when:
    start <= t < end

Therefore, if one meeting ends at time t and another starts at
the same time t, they do not overlap.

Algorithm:
Use a sweep-line over start/end events.
End events at the same timestamp occur before start events.

Key constraints:
- Intervals are represented as (start, end).
- start must not be greater than end.
- Zero-length intervals [t, t) are valid but contain no active time.
- Empty input is allowed and produces zero concurrency.
- Disconnected intervals are allowed.
- Results are deterministic.
- peak_times are sorted.
- Only standard-library functionality is used.
- No network access, APIs, external services, randomness, or
  human interaction are required.

Output:
{
    "max_concurrent": int,
    "peak_times": list
}

For empty input:
{
    "max_concurrent": 0,
    "peak_times": []
}

Tie-breaking:
At the same timestamp, end events are processed before start events.
A timestamp is reported when the active meeting count begins a period
at the maximum concurrency. Each timestamp appears at most once.
"""


from typing import Any, Iterable, Tuple


def interval_conflict_analyzer(
    intervals: Iterable[Tuple[Any, Any]]
) -> dict:
    """
    Return the maximum simultaneous meetings and the sorted times
    at which that maximum begins.