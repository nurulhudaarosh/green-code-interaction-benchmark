Meeting Sweep-Line Solver
==========================

PROBLEM
-------
We are given a list of half-open meeting intervals [start, end), where
`start` and `end` are numeric timestamps and start < end for every meeting.
A meeting occupies time exactly on the interval [start, end): it is
"active" at any instant t such that start <= t < end. Because the
intervals are half-open, a meeting that ends at time t does NOT overlap
with a different meeting that starts at that same time t.

We must find:
  1. The maximum number of meetings that are simultaneously active at
     any single instant in time (call this M).
  2. The sorted, de-duplicated list of timestamps at which the number of
     simultaneously active meetings first rises to reach M. (If the
     count reaches M, later drops, and later rises to M again at a
     different timestamp, that later timestamp is included too.)

KEY CONSTRAINTS
----------------
- Intervals are half-open: [start, end). A meeting is NOT counted as
  active at its own end time.
- Every meeting must satisfy start < end (zero-length or inverted
  meetings are invalid and rejected).
- Tie-breaking rule at a shared timestamp: all "end" events at a given
  time must be processed (removing meetings from the active set) BEFORE
  any "start" events at that same time are processed (adding meetings to
  the active set). This correctly reflects the half-open semantics.
- Determinism: no randomness, no network/API/service calls, no external
  input beyond the given interval list; the same input must always
  produce the same output.
- Standard library only.

REQUIRED OUTPUT
----------------
A tuple (max_count, begin_times):
  - max_count: an integer, the maximum number of simultaneously active
    meetings.
  - begin_times: a sorted list of the distinct timestamps at which the
    active-meeting count first climbs to max_count.

ALGORITHM (sweep line over start/end events)
---------------------------------------------
1. Validate input: every interval must have start < end.
2. Build two kinds of events per meeting:
       (start, +1)   -- a meeting becomes active
       (end,   -1)   -- a meeting stops being active
3. Sort all events primarily by timestamp. For events sharing the same
   timestamp, process -1 (end) events strictly before +1 (start) events,
   since a meeting ending at t no longer counts as active at t, while a
   meeting starting at t does count as active at t.
4. Sweep through time in order of distinct timestamps. At each distinct
   timestamp, apply ALL deltas that occur at that timestamp at once
   (first the removals, then the additions) to get the new active count.
5. Track the running maximum count seen so far:
     - If the new count exceeds the running maximum, update the maximum
       and reset the list of "begin times" to just this timestamp.
     - If the new count equals the running maximum AND the count just
       increased to reach it at this timestamp (i.e. it was lower before
       this timestamp's updates), record this timestamp as another
       "begin time".
     - If the new count is lower than or merely holds at a value that
       isn't a fresh climb to the maximum, do nothing.
6. Return the maximum count and the sorted list of begin times.

This runs in O(n log n) time due to sorting the 2n events, and O(n)
space, which is optimal for this class of interval-sweep problems.