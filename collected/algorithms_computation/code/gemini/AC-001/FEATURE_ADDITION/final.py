from typing import List, Tuple, Dict, Any, Union, Optional

def analyze_interval_conflicts(
    intervals: List[Tuple[int, int]], 
    include_summary: bool = False
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, Any]]]:
    """
    Analyzes half-open meeting intervals [start, end) to compute maximum simultaneous 
    meetings and peak concurrency start timestamps, with an optional deterministic 
    operation summary.

    Args:
        intervals: List of tuples representing half-open intervals [start, end).
        include_summary: If True, appends an operation_summary dictionary to the output.

    Returns:
        If include_summary is False:
            Tuple[int, List[int]] -> (max_active, peak_starts)
        If include_summary is True:
            Tuple[int, List[int], Dict[str, Any]] -> (max_active, peak_starts, operation_summary)
    """
    # Track metrics for deterministic operation summary
    valid_intervals_count = 0
    events = []

    for start, end in intervals:
        if start < end:  # Valid half-open interval check
            valid_intervals_count += 1
            events.append((start, 1))   # +1 for START
            events.append((end, -1))    # -1 for END (processed first on tie)

    # Sort events: primary key time ascending, secondary key event type (-1 before +1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_active = 0
    current_active = 0
    peak_starts = []
    sweep_steps = 0

    for time, event_type in events:
        sweep_steps += 1
        previous_active = current_active
        current_active += event_type

        # Check if we hit a new maximum concurrency
        if current_active > max_active:
            max_active = current_active
            peak_starts = [time]
        # Check if we reached existing maximum concurrency from a lower count
        elif current_active == max_active and previous_active < max_active:
            peak_starts.append(time)

    # Original fields
    result = (max_active, peak_starts)

    # Conditionally compute and append operation summary
    if include_summary:
        import math
        num_events = len(events)
        # Theoretical upper bound on sort operations: N * log2(N)
        sort_ops = math.ceil(num_events * math.log2(num_events)) if num_events > 1 else 0
        
        operation_summary = {
            "intervals_processed": valid_intervals_count,
            "events_generated": num_events,
            "sort_comparisons_bound": sort_ops,
            "sweep_steps": sweep_steps,
            "total_major_operations": num_events + sort_ops + sweep_steps
        }
        return (max_active, peak_starts, operation_summary)

    return result


if __name__ == "__main__":
    test_intervals = [(1, 5), (2, 6), (4, 8), (6, 9)]

    # 1. Default execution (preserves exact original output contract)
    max_c, starts = analyze_interval_conflicts(test_intervals)
    print("Standard Output:")
    print(f"Max Active: {max_c}, Peak Starts: {starts}\n")

    # 2. Execution with optional operation summary feature enabled
    max_c, starts, summary = analyze_interval_conflicts(test_intervals, include_summary=True)
    print("Output with Operation Summary:")
    print(f"Max Active: {max_c}")
    print(f"Peak Starts: {starts}")
    print("Operation Summary:", summary)