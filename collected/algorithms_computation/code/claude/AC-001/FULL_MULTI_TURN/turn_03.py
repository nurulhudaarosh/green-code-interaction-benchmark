"""
Interval Conflict Analyzer
---------------------------
Sweep-line solution: maximum simultaneous meetings and the sorted
start-times at which that maximum is reached, for half-open intervals [start, end).

Rule enforced: at any timestamp, END events are applied before START events,
since [start, end) means a meeting ending at t does not overlap one
starting at t. This is enforced structurally (separate end/start delta maps
processed in a fixed end-then-start order per timestamp).

New (opt-in) feature: when include_operation_summary=True, an additional
`operation_summary` dict is returned, counting major computational
decisions/operations made by the sweep. When the flag is False (default),
behavior and return shape are identical to the original implementation.

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
                   the return value is unchanged from the original
                   two-element (max_count, start_times) form.

    Returns:
        If include_operation_summary is False:
            (max_count, start_times)
        If include_operation_summary is True:
            (max_count, start_times, operation_summary)

        max_count        : maximum number of meetings active at once
                            (0 if no valid intervals).
        start_times       : sorted list of distinct meeting-start timestamps
                            at which the active count equals max_count
                            immediately after that timestamp's events are
                            processed (end events applied before start
                            events at ties).
        operation_summary : dict with keys:
                            - "timestamps_swept": number of distinct
                              timestamps processed by the sweep.
                            - "end_events_applied": number of end-event
                              decrements applied (one per timestamp that
                              has at least one ending meeting).
                            - "start_events_applied": number of start-event
                              increments applied (one per timestamp that
                              has at least one starting meeting).
                            - "max_updates": number of times the running
                              maximum was increased during the sweep.
                            - "start_time_checks": number of start
                              timestamps checked for qualification against
                              max_count.
    """
    delta_end = defaultdict(int)
    delta_start = defaultdict(int)

    for start, end in intervals:
        if start >= end:
            continue  # not a real interval, contributes no overlap
        delta_start[start] += 1
        delta_end[end] += 1

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
    count_after_time = {}  # timestamp -> count right after processing it

    # Operation counters (only meaningful/used when summary is requested,
    # but computed unconditionally since they are cheap and side-effect-free;
    # this keeps the sweep logic identical in both modes).
    timestamps_swept = 0
    end_events_applied = 0
    start_events_applied = 0
    max_updates = 0

    for t in all_times:
        timestamps_swept += 1

        # Structural tie-break: ends are always subtracted before starts
        # are added, at every timestamp, unconditionally.
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
    """Deterministic regression tests: original behavior + new feature."""

    # --- Original behavior must be unchanged when flag is default/False ---

    meetings = [(1, 3), (3, 5)]
    result = max_concurrent_meetings(meetings)
    assert result == (1, [1, 3]), result
    result = max_concurrent_meetings(meetings, include_operation_summary=False)
    assert result == (1, [1, 3]), result  # explicit False identical to default

    meetings = [(1, 5), (2, 6), (5, 8), (4, 7)]
    result = max_concurrent_meetings(meetings)
    assert result == (3, [4]), result

    meetings = [(0, 10), (0, 10), (5, 15), (20, 25), (20, 25)]
    result = max_concurrent_meetings(meetings)
    assert result == (2, [0, 20]), result

    assert max_concurrent_meetings([]) == (0, [])

    meetings = [(3, 3), (1, 2)]
    result = max_concurrent_meetings(meetings)
    assert result == (1, [1]), result

    # --- New feature: operation_summary, opt-in only ---

    meetings = [(1, 3), (3, 5)]
    max_count, start_times, summary = max_concurrent_meetings(
        meetings, include_operation_summary=True
    )
    assert (max_count, start_times) == (1, [1, 3])
    # Distinct timestamps: 1, 3, 5 -> 3 swept
    assert summary["timestamps_swept"] == 3, summary
    # Ends occur at t=3 and t=5 -> 2 end-applications
    assert summary["end_events_applied"] == 2, summary
    # Starts occur at t=1 and t=3 -> 2 start-applications
    assert summary["start_events_applied"] == 2, summary
    # Max goes 0->1 at t=1, stays 1 thereafter -> 1 update
    assert summary["max_updates"] == 1, summary
    # Two distinct start timestamps checked
    assert summary["start_time_checks"] == 2, summary

    # Empty input with summary requested
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

    print("All self-tests passed.")


if __name__ == "__main__":
    _self_test()

    example = [(1, 5), (2, 6), (5, 8), (4, 7)]

    # Original usage (unchanged)
    max_count, start_times = max_concurrent_meetings(example)
    print(f"Meetings: {example}")
    print(f"Max concurrent meetings: {max_count}")
    print(f"Start times achieving max: {start_times}")

    # New opt-in usage
    max_count, start_times, operation_summary = max_concurrent_meetings(
        example, include_operation_summary=True
    )
    print(f"Operation summary: {operation_summary}")