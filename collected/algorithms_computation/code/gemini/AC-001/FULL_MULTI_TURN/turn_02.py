from typing import List, Tuple

def max_simultaneous_meetings(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    """
    Finds the maximum number of simultaneous active meetings and the sorted 
    timestamps where that maximum begins for half-open intervals [start, end).
    
    Deterministic tie handling: End events at timestamp T are processed 
    strictly before Start events at timestamp T.
    """
    if not intervals:
        return 0, []

    # 1. Generate events: (timestamp, delta)
    # delta = -1 for END, +1 for START.
    events = []
    for start, end in intervals:
        events.append((start, 1))
        events.append((end, -1))

    # 2. Sort primary by timestamp (asc), secondary by delta (asc: -1 before +1)
    events.sort(key=lambda x: (x[0], x[1]))

    max_active = 0
    current_active = 0
    max_starts = []

    # 3. Process sweep-line events
    for time, delta in events:
        current_active += delta

        # Trigger update only on start events reaching or exceeding peak
        if delta == 1:
            if current_active > max_active:
                max_active = current_active
                max_starts = [time]
            elif current_active == max_active:
                if not max_starts or max_starts[-1] != time:
                    max_starts.append(time)

    return max_active, max_starts


if __name__ == "__main__":
    # Test 1: Boundary point tie-breaking
    # (1,4) and (2,4) end at 4; (4,6) and (4,7) start at 4.
    test_1 = [(1, 4), (2, 4), (4, 6), (4, 7)]
    max_cnt1, starts1 = max_simultaneous_meetings(test_1)
    print(f"Test 1 -> Max Active: {max_cnt1}, Starts At: {starts1}")
    # Expected: Max Active: 2, Starts At: [2]

    # Test 2: Multiple peak regions
    test_2 = [(1, 4), (2, 5), (4, 7), (3, 8), (5, 9)]
    max_cnt2, starts2 = max_simultaneous_meetings(test_2)
    print(f"Test 2 -> Max Active: {max_cnt2}, Starts At: {starts2}")
    # Expected: Max Active: 3, Starts At: [3, 5]