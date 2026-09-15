from typing import List, Tuple


def analyze_intervals(
    intervals: List[Tuple[int, int]]
) -> Tuple[int, List[int]]:
    events = []

    for start, end in intervals:
        if start >= end:
            raise ValueError("Each interval must satisfy start < end.")

        events.append((start, 1))   # start
        events.append((end, -1))    # end

    # At the same timestamp, -1 (end) is processed before +1 (start).
    events.sort(key=lambda event: (event[0], event[1]))

    active = 0
    maximum = 0
    maximum_times = []

    i = 0

    while i < len(events):
        time = events[i][0]

        # Apply all events at this timestamp.
        # End events are already ordered before start events.
        while i < len(events) and events[i][0] == time:
            active += events[i][1]
            i += 1

        if active > maximum:
            maximum = active
            maximum_times = [time]
        elif active == maximum and active > 0:
            if not maximum_times or maximum_times[-1] != time:
                maximum_times.append(time)

    return maximum, maximum_times


def main() -> None:
    intervals = [
        (1, 3),
        (3, 5)
    ]

    maximum, times = analyze_intervals(intervals)

    print(maximum)
    print(times)


if __name__ == "__main__":
    main()