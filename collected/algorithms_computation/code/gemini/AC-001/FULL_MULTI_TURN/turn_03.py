import math
from typing import List, Tuple, Dict, Any, Union

def max_simultaneous_meetings(
    intervals: List[Tuple[int, int]], 
    include_summary: bool = False
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, Any]]]:
    """
    Finds the peak number of simultaneous meetings and sorted timestamps 
    where the peak begins for half-open intervals [start, end).

    :param intervals: List of tuples/lists representing [start, end)
    :param include_summary: If True, returns an operational summary dictionary as a 3rd element.
    :return: (max_active, max_starts) OR (max_active, max_starts, operation_summary)
    """
    if not intervals:
        summary = {
            "total_events": 0,
            "sorting_comparisons_bound": 0,
            "state_transitions": 0,
            "peak_updates": 0,
            "peak_start_recordings": 0
        }
        return (0, [], summary) if include_summary else (0, [])

    # 1. Event Generation: (timestamp, delta)
    # END = -1, START = +1. Sorting -1 before +1 enforces half-open interval rules.
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))

    total_events = len(events)
    # Estimate comparison ops for Timsort/MergeSort: N * log2(N)
    sorting_ops = round(total_events * math.log2(total_events), 2) if total_events > 0 else 0

    # 2. Deterministic Sort: Primary by time (asc), secondary by delta (asc: -1 before +1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_active = 0
    current_active = 0
    max_starts = []
    
    # Operation metrics counters
    state_transitions = 0
    peak_updates = 0
    peak_start_recordings = 0

    # 3. Sweep-Line Traversal
    for time, delta in events:
        state_transitions += 1
        current_active += delta

        # Only evaluate start events for peak updates
        if delta == 1:
            if current_active > max_active:
                max_active = current_active
                max_starts = [time]
                peak_updates += 1
                peak_start_recordings = 1
            elif current_active == max_active:
                if not max_starts or max_starts[-1] != time:
                    max_starts.append(time)
                    peak_start_recordings += 1

    if include_summary:
        operation_summary = {
            "total_events": total_events,
            "sorting_comparisons_bound": sorting_ops,
            "state_transitions": state_transitions,
            "peak_updates": peak_updates,
            "peak_start_recordings": peak_start_recordings
        }
        return max_active, max_starts, operation_summary

    return max_active, max_starts


if __name__ == "__main__":
    test_intervals = [
        (1, 4),
        (2, 5),
        (4, 7),
        (3, 8),
        (5, 9)
    ]

    # Default call (Backwards Compatible)
    max_cnt, starts = max_simultaneous_meetings(test_intervals)
    print("--- Default Output ---")
    print(f"Max Active: {max_cnt}")
    print(f"Starts At:  {starts}\n")

    # Call with feature enabled
    max_cnt, starts, summary = max_simultaneous_meetings(test_intervals, include_summary=True)
    print("--- Output with Summary ---")
    print(f"Max Active: {max_cnt}")
    print(f"Starts At:  {starts}")
    print("Operation Summary:")
    for key, val in summary.items():
        print(f"  - {key}: {val}")