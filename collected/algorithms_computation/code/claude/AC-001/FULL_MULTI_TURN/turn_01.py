Sweep-line solution: maximum simultaneous meetings and the sorted
start-times at which that maximum is reached, for half-open intervals [start, end).

Rule: at any timestamp, END events are applied before START events,
since [start, end) means a meeting ending at t does not overlap one
starting at t.

Deterministic, standard-library only. No network, no randomness, no I/O input.
"""

from collections import defaultdict
from typing import List, Tuple, Sequence


def max_concurrent_meetings(
    intervals: Sequence[Tuple[float, float]]
) -> Tuple[int, List[float]]:
    """
    Args:
        intervals: sequence of (start, end) pairs, half-open [start, end).
                   start/end may be int or float. Intervals with
                   start >= end are ignored (zero or negative duration).

    Returns:
        (max_count, start_times)
        max_count   : maximum number of meetings active at once (0 if no
                      valid intervals).
        start_times : sorted list of distinct meeting-start timestamps at
                      which the active count equals max_count immediately
                      after that timestamp's events are processed.