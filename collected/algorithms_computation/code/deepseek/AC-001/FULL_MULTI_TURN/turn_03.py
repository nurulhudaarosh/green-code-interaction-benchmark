"""
Problem: Interval Conflict Analyzer

Given half-open meeting intervals [start, end), find the maximum number of
simultaneously active meetings and the sorted times at which that maximum begins.

Original required outputs:
- maximum_count: The maximum number of simultaneously active meetings (int)
- start_times: Sorted list of times at which the maximum count begins (List[int])
- For empty input: Return (0, [])

Additional feature (optional): operation_summary
- When requested (by passing include_summary=True), return a deterministic
  summary containing the number of major computational decisions/operations
  made by the algorithm.
- For this implementation, operation_summary tracks:
  * total_events: Number of events processed (2 * number of intervals)
  * distinct_timestamps: Number of distinct timestamps with events
  * start_events: Number of start events
  * end_events: Number of end events
  * timestamps_with_starts: Number of timestamps where at least one meeting starts
  * max_count: The maximum count found (redundant but useful for verification)

- When include_summary=False (default): Return only (maximum_count, start_times)
- When include_summary=True: Return (maximum_count, start_times, operation_summary)

Algorithm: Sweep-line over events
1. Create events: (time, type) where type=0 for END, type=1 for START
2. Sort by (time, type) so END (0) comes before START (1) at same timestamp
3. Sweep through events, maintaining current active count
4. Track maximum count and the start times when this maximum is first achieved
5. For each START event, record the time if count after adding equals max_count
6. Count operations: distinct timestamps, start events, end events, etc.

Time complexity: O(n log n) due to sorting
Space complexity: O(n)
"""

from typing import List, Tuple, Dict, Union, Optional


def find_max_active_meetings(
    intervals: List[Tuple[int, int]], 
    include_summary: bool = False
) -> Union[Tuple[int, List[int]], Tuple[int, List[int], Dict[str, int]]]:
    """
    Find the maximum number of simultaneously active meetings and the sorted
    times at which that maximum begins.

    Args:
        intervals: List of [start, end) meeting intervals
        include_summary: If True, include operation_summary in the return value

    Returns:
        If include_summary=False: (max_count, list_of_start_times)
        If include_summary=True: (max_count, list_of_start_times, operation_summary)
        Returns (0, []) or (0, [], {}) for empty input
    """
    # Initialize operation counters
    total_events = 0
    distinct_timestamps = 0
    start_events = 0
    end_events = 0
    timestamps_with_starts = 0
    
    if not intervals:
        if include_summary:
            return 0, [], {
                'total_events': 0,
                'distinct_timestamps': 0,
                'start_events': 0,
                'end_events': 0,
                'timestamps_with_starts': 0,
                'max_count': 0
            }
        return 0, []

    # Create events: (time, type)
    # type: 0 for END, 1 for START (END before START at same timestamp)
    events = []
    for start, end in intervals:
        events.append((start, 1))  # START event
        events.append((end, 0))    # END event
        start_events += 1
        end_events += 1
        total_events += 2

    # Sort by time, then by type (END=0 comes before START=1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_count = 0
    current_count = 0
    result_times = []

    i = 0
    while i < len(events):
        time = events[i][0]
        distinct_timestamps += 1
        
        # Process all END events at this timestamp first
        has_end_at_time = False
        while i < len(events) and events[i][0] == time and events[i][1] == 0:
            current_count -= 1
            has_end_at_time = True
            i += 1
        
        # Count START events at this timestamp
        start_count = 0
        has_start_at_time = False
        while i < len(events) and events[i][0] == time and events[i][1] == 1:
            current_count += 1
            start_count += 1
            has_start_at_time = True
            i += 1
        
        # Track timestamps with start events
        if has_start_at_time:
            timestamps_with_starts += 1
        
        # After processing all events at this timestamp, update max and results
        if start_count > 0:  # Only consider timestamps where meetings actually start
            if current_count > max_count:
                # New maximum reached
                max_count = current_count
                result_times = [time]
            elif current_count == max_count:
                # Same maximum reached at this start time
                # Avoid duplicates: check if this time is already the last recorded
                if not result_times or result_times[-1] != time:
                    result_times.append(time)

    # Prepare operation summary
    if include_summary:
        operation_summary = {
            'total_events': total_events,
            'distinct_timestamps': distinct_timestamps,
            'start_events': start_events,
            'end_events': end_events,
            'timestamps_with_starts': timestamps_with_starts,
            'max_count': max_count
        }
        return max_count, result_times, operation_summary
    
    return max_count, result_times


def main():
    """Test the function with comprehensive test cases."""
    
    print("=" * 70)
    print("INTERVAL CONFLICT ANALYZER - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Test case 1: Basic overlapping intervals
    intervals1 = [(0, 3), (1, 4), (2, 5), (3, 6)]
    print(f"\nTest 1: Basic overlapping intervals")
    print(f"Intervals: {intervals1}")
    
    # Without summary
    count1, times1 = find_max_active_meetings(intervals1)
    print(f"Without summary: max={count1}, times={times1}")
    
    # With summary
    count1s, times1s, summary1 = find_max_active_meetings(intervals1, include_summary=True)
    print(f"With summary: max={count1s}, times={times1s}")
    print(f"Operation summary: {summary1}")
    assert count1 == 3, f"Expected max=3, got {count1}"
    assert times1 == [2, 3], f"Expected times=[2, 3], got {times1}"
    print("✓ PASSED")
    
    # Test case 2: Touch at endpoints (half-open intervals)
    intervals2 = [(0, 5), (5, 10), (10, 15)]
    count2, times2 = find_max_active_meetings(intervals2)
    print(f"\nTest 2: Touch at endpoints (half-open)")
    print(f"Intervals: {intervals2}")
    print(f"Result: max={count2}, times={times2}")
    assert count2 == 1, f"Expected max=1, got {count2}"
    assert times2 == [0, 5, 10], f"Expected times=[0, 5, 10], got {times2}"
    print("✓ PASSED")
    
    # Test case 3: Multiple meetings starting at same time
    intervals3 = [(0, 5), (0, 6), (0, 7), (1, 2)]
    count3, times3 = find_max_active_meetings(intervals3)
    print(f"\nTest 3: Multiple meetings starting at same time")
    print(f"Intervals: {intervals3}")
    print(f"Result: max={count3}, times={times3}")
    assert count3 == 3, f"Expected max=3, got {count3}"
    assert times3 == [0], f"Expected times=[0], got {times3}"
    print("✓ PASSED")
    
    # Test case 4: Empty input
    intervals4 = []
    count4, times4 = find_max_active_meetings(intervals4)
    print(f"\nTest 4: Empty input")
    print(f"Intervals: {intervals4}")
    print(f"Result: max={count4}, times={times4}")
    assert count4 == 0, f"Expected max=0, got {count4}"
    assert times4 == [], f"Expected times=[], got {times4}"
    print("✓ PASSED")
    
    # Test with summary for empty input
    count4s, times4s, summary4 = find_max_active_meetings(intervals4, include_summary=True)
    print(f"With summary for empty: max={count4s}, times={times4s}")
    print(f"Operation summary: {summary4}")
    assert summary4['total_events'] == 0, "Expected 0 total events"
    print("✓ PASSED")
    
    # Test case 5: End events before start events at same timestamp
    intervals5 = [(0, 2), (2, 4), (2, 3)]
    count5, times5 = find_max_active_meetings(intervals5)
    print(f"\nTest 5: End before start at same timestamp")
    print(f"Intervals: {intervals5}")
    print(f"Result: max={count5}, times={times5}")
    assert count5 == 2, f"Expected max=2, got {count5}"
    assert times5 == [0], f"Expected times=[0], got {times5}"
    print("✓ PASSED")
    
    # Test case 6: All meetings non-overlapping
    intervals6 = [(0, 1), (2, 3), (4, 5)]
    count6, times6 = find_max_active_meetings(intervals6)
    print(f"\nTest 6: All non-overlapping")
    print(f"Intervals: {intervals6}")
    print(f"Result: max={count6}, times={times6}")
    assert count6 == 1, f"Expected max=1, got {count6}"
    assert times6 == [0, 2, 4], f"Expected times=[0, 2, 4], got {times6}"
    print("✓ PASSED")
    
    # Test case 7: Complex overlapping with multiple max times
    intervals7 = [(0, 10), (1, 3), (2, 4), (5, 7), (6, 8)]
    count7, times7 = find_max_active_meetings(intervals7)
    print(f"\nTest 7: Complex overlapping with multiple max times")
    print(f"Intervals: {intervals7}")
    print(f"Result: max={count7}, times={times7}")
    assert count7 == 2, f"Expected max=2, got {count7}"
    assert times7 == [1, 2, 5, 6], f"Expected times=[1, 2, 5, 6], got {times7}"
    print("✓ PASSED")
    
    # Test case 8: Large number of intervals (demonstrating summary)
    intervals8 = [(i, i+2) for i in range(10)]
    count8, times8, summary8 = find_max_active_meetings(intervals8, include_summary=True)
    print(f"\nTest 8: Large dataset (10 intervals)")
    print(f"Intervals: {intervals8[:5]}... (truncated)")
    print(f"Result: max={count8}, times={times8}")
    print(f"Operation summary: {summary8}")
    assert summary8['total_events'] == 20, "Expected 20 total events"
    assert summary8['start_events'] == 10, "Expected 10 start events"
    assert summary8['end_events'] == 10, "Expected 10 end events"
    print("✓ PASSED")
    
    # Test case 9: Verify that default behavior (without summary) unchanged
    intervals9 = [(1, 2), (2, 3), (3, 4)]
    result9_default = find_max_active_meetings(intervals9)
    result9_summary = find_max_active_meetings(intervals9, include_summary=True)
    print(f"\nTest 9: Verify default vs summary behavior")
    print(f"Default result: {result9_default}")
    print(f"Summary result (first two elements): {result9_summary[:2]}")
    assert result9_default[0] == result9_summary[0], "Max count should match"
    assert result9_default[1] == result9_summary[1], "Times should match"
    print("✓ PASSED - Summary feature doesn't affect original outputs")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✓")
    print("=" * 70)
    
    # Additional demonstration of operation summary values
    print("\n" + "=" * 70)
    print("OPERATION SUMMARY EXPLANATION")
    print("=" * 70)
    print("\nThe operation_summary dictionary contains:")
    print("  • total_events: Total number of events processed (2 * number of intervals)")
    print("  • distinct_timestamps: Number of unique timestamps with events")
    print("  • start_events: Number of start events (equals number of intervals)")
    print("  • end_events: Number of end events (equals number of intervals)")
    print("  • timestamps_with_starts: Number of timestamps where at least one meeting starts")
    print("  • max_count: The maximum number of simultaneous meetings (redundant)")
    print("\nThese values are deterministic and can be used for verification or debugging.")


if __name__ == "__main__":
    main()