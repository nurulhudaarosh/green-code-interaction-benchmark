Maximum Simultaneous Meetings (Sweep-Line)
===========================================

PROBLEM
-------
We are given a list of meetings, each represented as a half-open interval
[start, end), meaning the meeting occupies time from `start` (inclusive)
up to but not including `end`. Because intervals are half-open, a meeting
ending at time t and another meeting starting at time t do NOT overlap
(the first one has already vacated the slot).

We must compute:
  1. The maximum number of meetings that are simultaneously active at any
     single point in time.
  2. The sorted list of distinct time points at which that maximum count
     is first reached (each time the active count transitions UP into
     the maximum level — including cases where it dips below the maximum
     and later climbs back up to it again).

KEY CONSTRAINTS
----------------
- Intervals are half-open: [start, end), start < end for a valid meeting.
- Tie-breaking rule at equal timestamps: an "end" event at time t must be
  processed BEFORE a "start" event at time t, since the departing meeting
  no longer occupies time t.
- Solution must be deterministic: no randomness, no wall-clock time, no
  network/API calls, no human interaction — pure function of the input.
- Only the Python standard library may be used.

REQUIRED OUTPUT
----------------
A tuple: (max_count: int, begin_times: List[float/int])
where begin_times is sorted ascending and contains each timestamp at
which the running active-meeting count rises to reach max_count.

ALGORITHM (Sweep-Line)
-----------------------
1. Convert each interval [s, e) into two events: (s, +1) "start" and
   (e, -1) "end".
2. Sort all events by (time, type) where "end" (-1) sorts before
   "start" (+1) at the same timestamp — this encodes the half-open
   semantics.
3. Group events by identical timestamp and sum their deltas, producing
   a sequence of (time, net_delta) pairs in chronological order.
4. Sweep once, accumulating a running `count`, to determine the global
   maximum count reached.
5. Sweep again, tracking the count before and after each timestamp's
   delta is applied. Whenever the count crosses INTO the maximum
   (i.e., previous count < max_count and new count == max_count),
   record that timestamp as a "begin" point.
6. Return the maximum and the sorted list of begin points (already in
   ascending order since we process events chronologically).

Time complexity: O(n log n) for sorting; O(n) for the two sweeps.
Space complexity: O(n).