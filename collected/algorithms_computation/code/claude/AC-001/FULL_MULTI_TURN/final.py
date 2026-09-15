"""
Interval Conflict Analyzer
---------------------------
Sweep-line solution: maximum simultaneous meetings and the sorted
start-times at which that maximum is reached, for half-open intervals [start, end).

Rule enforced: at any timestamp, END events are applied before START events,
since [start, end) means a meeting ending at t does not overlap one
starting at t. Enforced structurally (separate end/start delta maps,
processed end-then-start per timestamp) -- never via sort/insertion order.

Explicitly handled edge cases:
  - empty input
  - smallest permitted input (a single valid interval)
  - all-invalid input (every interval has start >= end)
  - disconnected intervals (no two intervals overlap or touch)
  - mix of valid and invalid intervals

Opt-in feature: include_operation_summary=True returns a third element,
`operation_summary`, with deterministic sweep operation counts. Default
(False) preserves the original two-element return shape exactly.

Deterministic, standard-library only. No network, randomness, or I/O input.
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Union, Sequence


def max_concurrent_meetings(
    intervals: Sequence[Tuple[float, float]],
    include_operation_summary: bool = False,
) -> Union[
    Tuple[int, List[float]],
    Tuple[int, List[float], Dict[str, int]],
]:
    """
    Args:
        intervals: sequence of (start, end) pairs, half-open [start, end).
                   start/end may be int or float. Intervals with
                   start >= end are ignored (zero or negative duration).
        include_operation_summary: if True, also return a third element,
                   `operation_summary`, a dict of deterministic operation
                   counts describing the sweep's work. If False (default),
                   the return value is the original two-element form.

    Returns:
        If include_operation_summary is False:
            (max_count, start_times)
        If include_operation_summary is True:
            (max_count, start_times, operation_summary)

        max_count        : maximum number of meetings active at once
                            (0 if no valid intervals -- covers empty input
                            and all-invalid input alike).
        start_times       : sorted list of distinct meeting-start timestamps
                            at which the active count equals max_count
                            immediately after that timestamp's events are
                            processed (end events applied before start
                            events at ties). For disconnected intervals,
                            every interval's start qualifies since each
                            reaches the shared maximum independently.
        operation_summary : dict with keys:
                            - "timestamps_swept"
                            - "end_events_applied"
                            - "start_events_applied"
                            - "max_updates"
                            - "start_time_checks"
    """
    delta_end = defaultdict(int)
    delta_start = defaultdict(int)

    for start, end in intervals:
        if start >= end:
            continue  # invalid/degenerate interval: contributes nothing
        delta_start[start] += 1
        delta_end[end] += 1

    # Covers both "empty input" and "all intervals invalid" cases uniformly.
    if not delta_start:
        if include_operation_summary:
            return 0, [], {
                "timestamps_swept": 0,
                "end_events_applied": 0,
                "start_events_applied": 0,
                "max_updates": 0,
                "start_time_checks": 0,
            }
        return 0, []

    all_times = sorted(set(delta_start) | set(delta_end))

    count = 0
    max_count = 0
    count_after_time = {}

    timestamps_swept = 0
    end_events_applied = 0
    start_events_applied = 0
    max_updates = 0

    for t in all_times:
        timestamps_swept += 1

        # End-before-start at equal timestamps, applied structurally.
        if t in delta_end:
            count -= delta_end[t]
            end_events_applied += 1
        if t in delta_start:
            count += delta_start[t]
            start_events_applied += 1

        count_after_time[t] = count
        if count > max_count:
            max_count = count
            max_updates += 1

    start_time_checks = 0
    start_times = []
    for t in sorted(delta_start):
        start_time_checks += 1
        if count_after_time[t] == max_count:
            start_times.append(t)

    if not include_operation_summary:
        return max_count, start_times

    operation_summary = {
        "timestamps_swept": timestamps_swept,
        "end_events_applied": end_events_applied,
        "start_events_applied": start_events_applied,
        "max_updates": max_updates,
        "start_time_checks": start_time_checks,
    }
    return max_count, start_times, operation_summary


def _self_test() -> None:
    """Regression tests: original behavior, tie-break rule, and new edge cases."""

    # --- Original / prior regression tests (unchanged) ---

    meetings = [(1, 3), (3, 5)]
    assert max_concurrent_meetings(meetings) == (1, [1, 3])

    meetings = [(1, 3), (3, 5), (5, 7)]
    assert max_concurrent_meetings(meetings) == (1, [1, 3, 5])

    meetings = [(1, 5), (2, 6), (5, 8), (4, 7)]
    assert max_concurrent_meetings(meetings) == (3, [4])

    meetings = [(0, 10), (0, 10), (5, 15), (20, 25), (20, 25)]
    assert max_concurrent_meetings(meetings) == (2, [0, 20])

    meetings = [(1, 10), (2, 5), (5, 8)]
    assert max_concurrent_meetings(meetings) == (2, [1, 2])

    # --- New edge cases ---

    # Empty input.
    result = max_concurrent_meetings([])
    assert result == (0, []), result

    # Smallest permitted input: exactly one valid interval.
    result = max_concurrent_meetings([(0, 1)])
    assert result == (1, [0]), result

    # Smallest positive width interval.
    result = max_concurrent_meetings([(0, 1e-9)])
    assert result == (1, [0]), result

    # All intervals invalid (start >= end for every entry) -> same as empty.
    result = max_concurrent_meetings([(5, 5), (3, 2), (7, 7)])
    assert result == (0, []), result

    # Mix of valid and invalid intervals: invalid ones silently dropped.
    result = max_concurrent_meetings([(1, 1), (2, 4)])
    assert result == (1, [2]), result

    # Disconnected intervals: no overlap or touching at all.
    # Every start independently reaches the shared max of 1.
    result = max_concurrent_meetings([(0, 1), (10, 11), (20, 21)])
    assert result == (1, [0, 10, 20]), result

    # Disconnected intervals given out of order -> start_times still sorted.
    result = max_concurrent_meetings([(20, 21), (0, 1), (10, 11)])
    assert result == (1, [0, 10, 20]), result

    # Disconnected intervals of differing (but individually non-overlapping)
    # duplicate counts still only ever reach max_count = 1 each.
    result = max_concurrent_meetings([(0, 5), (100, 200), (300, 301)])
    assert result == (1, [0, 100, 300]), result

    # --- operation_summary opt-in tests, including edge cases ---

    max_count, start_times, summary = max_concurrent_meetings(
        [], include_operation_summary=True
    )
    assert (max_count, start_times) == (0, [])
    assert summary == {
        "timestamps_swept": 0,
        "end_events_applied": 0,
        "start_events_applied": 0,
        "max_updates": 0,
        "start_time_checks": 0,
    }, summary

    max_count, start_times, summary = max_concurrent_meetings(
        [(5, 5), (3, 2)], include_operation_summary=True
    )
    assert (max_count, start_times) == (0, [])
    assert summary["timestamps_swept"] == 0, summary

    max_count, start_times, summary = max_concurrent_meetings(
        [(0, 1)], include_operation_summary=True
    )
    assert (max_count, start_times) == (1, [0])
    assert summary["timestamps_swept"] == 2, summary       # t=0, t=1
    assert summary["start_events_applied"] == 1, summary
    assert summary["end_events_applied"] == 1, summary
    assert summary["max_updates"] == 1, summary
    assert summary["start_time_checks"] == 1, summary

    max_count, start_times, summary = max_concurrent_meetings(
        [(0, 1), (10, 11), (20, 21)], include_operation_summary=True
    )
    assert (max_count, start_times) == (1, [0, 10, 20])
    assert summary["timestamps_swept"] == 6, summary        # 0,1,10,11,20,21
    assert summary["start_events_applied"] == 3, summary
    assert summary["end_events_applied"] == 3, summary
    assert summary["max_updates"] == 1, summary             # max hits 1 once, never rises again
    assert summary["start_time_checks"] == 3, summary

    print("All self-tests passed.")


if __name__ == "__main__":
    _self_test()

    example = [(1, 5), (2, 6), (5, 8), (4, 7)]
    max_count, start_times = max_concurrent_meetings(example)
    print(f"Meetings: {example}")
    print(f"Max concurrent meetings: {max_count}")
    print(f"Start times achieving max: {start_times}")

    disconnected = [(0, 1), (10, 11), (20, 21)]
    max_count, start_times, summary = max_concurrent_meetings(
        disconnected, include_operation_summary=True
    )
    print(f"Disconnected meetings: {disconnected}")
    print(f"Max concurrent meetings: {max_count}")
    print(f"Start times achieving max: {start_times}")
    print(f"Operation summary: {summary}")