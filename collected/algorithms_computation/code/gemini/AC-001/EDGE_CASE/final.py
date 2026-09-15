"""
Interval Conflict Analyzer (Sweep-Line Implementation)

Handles half-open intervals [start, end) with strict same-timestamp tie-breaking 
(END events processed before START events).
"""

from typing import List, Tuple


def max_simultaneous_meetings(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Finds the maximum number of simultaneous active meetings and the sorted 
    timestamps where that maximum overlap level begins.

    Args:
        intervals: List of half-open intervals [start, end).

    Returns:
        A tuple containing:
            - max_active (int): Maximum count of concurrent meetings.
            - start_times (List[int]): Sorted timestamps where max active count begins.
    """
    # Boundary Case 1: Empty input
    if not intervals:
        return 0, []

    # Step 1: Generate discrete sweep-line events
    # Event encoding: (timestamp, event_type)
    # event_type = -1 for END, +1 for START.
    # Because -1 < 1, Python sorting guarantees END events process before START events 
    # at identical timestamps.
    events = []
    for start, end in intervals:
        # Filter out invalid inverted intervals if present
        if end < start:
            raise ValueError(f"Invalid interval: start ({start}) > end ({end})")
        events.append((start, 1))
        events.append((end, -1))

    # Step 2: Deterministic sorting
    events.sort(key=lambda x: (x[0], x[1]))

    current_active = 0
    max_active = 0
    max_start_times = []

    # Step 3: Sweep line through timeline
    for time, event_type in events:
        prev_active = current_active
        current_active += event_type

        # Condition 1: Exceeded previous maximum -> reset start times tracking
        if current_active > max_active:
            max_active = current_active
            max_start_times = [time]
        # Condition 2: Reached current maximum peak from max_active - 1
        elif current_active == max_active and max_active > 0 and prev_active == max_active - 1:
            max_start_times.append(time)

    return max_active, max_start_times


# =====================================================================
# Unit Tests & Verification
# =====================================================================

def run_tests():
    test_cases = [
        {
            "name": "Empty Input (Disconnected/Empty structure)",
            "input": [],
            "expected": (0, [])
        },
        {
            "name": "Smallest Permitted Input (Single interval)",
            "input": [(5, 10)],
            "expected": (1, [5])
        },
        {
            "name": "Adjacent / Touch-at-boundary intervals [1, 5) and [5, 8)",
            "input": [(1, 5), (5, 8)],
            "expected": (1, [1, 5])
        },
        {
            "name": "Zero-length interval [5, 5) (Edge case)",
            "input": [(5, 5)],
            "expected": (0, [])
        },
        {
            "name": "Fully Disconnected Intervals",
            "input": [(1, 3), (10, 15), (20, 25)],
            "expected": (1, [1, 10, 20])
        },
        {
            "name": "Multiple Disconnected Peaks of Same Height",
            "input": [(1, 5), (2, 6), (10, 15), (11, 14)],
            "expected": (2, [2, 11])
        },
        {
            "name": "Negative and Zero Timestamps",
            "input": [(-10, -2), (-5, 0), (-3, 4)],
            "expected": (2, [-5, -3])
        },
        {
            "name": "Complex Multi-Peak Overlaps",
            "input": [(1, 5), (2, 6), (4, 8), (6, 9), (6, 10)],
            "expected": (3, [4])
        }
    ]

    print("Running Test Suite for Interval Conflict Analyzer...\n" + "=" * 60)
    all_passed = True
    for test in test_cases:
        actual = max_simultaneous_meetings(test["input"])
        passed = actual == test["expected"]
        status = "PASSED" if passed else "FAILED"
        if not passed:
            all_passed = False
        print(f"[{status}] {test['name']}")
        print(f"  Input:    {test['input']}")
        print(f"  Expected: {test['expected']}")
        print(f"  Actual:   {actual}\n")

    if all_passed:
        print("=" * 60 + "\nAll tests passed successfully!")
    else:
        print("=" * 60 + "\nSome tests failed.")


if __name__ == "__main__":
    run_tests()