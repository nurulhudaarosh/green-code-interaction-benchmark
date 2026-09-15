from typing import List, Tuple


def maximum_meetings(intervals: List[Tuple[int, int]]) -> Tuple[int, List[int]]:
    events = []

    for start, end in intervals:
        if start >= end:
            raise ValueError("Each interval must satisfy start < end.")

        events.append((start, 1))
        events.append((end, -1))

    # End events are processed before start events at the same time.
    events.sort(key=lambda event: (event[0], event[1]))

    active = 0
    maximum = 0
    maximum_times = []

    i = 0

    while i < len(events):
        time = events[i][0]

        while i < len(events) and events[i][0] == time:
            active += events[i][1]
            i += 1

        if active > maximum:
            maximum = active
            maximum_times = [time]
        elif active == maximum and maximum > 0:
            maximum_times.append(time)

    return maximum, maximum_times


def main():
    meetings = [
        (1, 5),
        (2, 6),
        (3, 4),
        (5, 7),
        (6, 8)
    ]

    maximum, times = maximum_meetings(meetings)

    print("Maximum simultaneous meetings:", maximum)
    print("Times at which maximum begins:", times)


if __name__ == "__main__":
    main()