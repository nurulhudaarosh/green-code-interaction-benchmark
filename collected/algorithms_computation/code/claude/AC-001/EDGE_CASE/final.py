Interval Conflict Analyzer
===========================

RESTATED PROBLEM
-----------------
We are given a collection of meeting intervals, each expressed as a
half-open interval [start, end) on the real (numeric) timeline, where
`start` and `end` are timestamps and start < end for every meeting. A
meeting is considered "active" at an instant t exactly when
start <= t < end (the end instant itself is excluded).

The Interval Conflict Analyzer must determine, across the entire
timeline spanned by the given meetings:

  1. The maximum number of meetings that are ever simultaneously
     active at any single instant in time (call this M, the "peak
     conflict count").
  2. The complete, sorted, de-duplicated list of timestamps at which
     the active-meeting count freshly climbs to reach M. "Freshly
     climbs" means the count was strictly lower immediately before
     this timestamp's events were applied and becomes exactly M once
     they are applied. If the count reaches M, later drops below M,
     and later climbs back to exactly M at a different timestamp, that
     later timestamp is also included.

KEY CONSTRAINTS
----------------
- Intervals are half-open: [start, end). A meeting is NOT counted as
  active at its own end time, so two meetings meeting exactly
  back-to-back (one's end equals another's start) never count as
  overlapping.
- Every meeting must satisfy start < end. Zero-length ([t, t)) or
  inverted (start > end) intervals are invalid and must be rejected.
- Tie-breaking rule at a shared timestamp: all "end" events at a given
  time are processed (removing meetings from the active set) strictly
  BEFORE any "start" events at that same time are processed (adding
  meetings to the active set). This reflects half-open semantics
  correctly and must be preserved exactly.
- Determinism: no randomness, no network/API/service calls, no
  external or interactive input beyond the given interval list; the
  same input must always produce the same output on every run.
- Standard library only.

DIFFICULT / EDGE CASES EXPLICITLY HANDLED
-------------------------------------------
- Smallest permitted input: a single valid meeting interval. With
  exactly one meeting, the peak conflict count is 1, and the single
  begin time is that meeting's own start timestamp. (An empty input,
  i.e. zero meetings, is also explicitly supported as a degenerate
  "smallest" case and yields a peak of 0 with no begin times, since
  there is never any active meeting to count.)
- Empty structure: `intervals = []` is valid input, not an error. It
  represents "no meetings scheduled" rather than a malformed request.
- Disconnected structures: meetings that form two or more separate
  clusters with time gaps between them (no meeting in one cluster ever
  overlaps a meeting in another cluster). The algorithm must still
  find the correct global peak count and, if that peak recurs
  identically in more than one disconnected cluster, must report every
  timestamp at which it is freshly reached -- not just the first one
  encountered chronologically.
- Fully disjoint meetings (every meeting is its own disconnected
  cluster, none overlapping any other at all): the peak is 1, and
  every meeting's start timestamp is a begin time, since the count
  climbs from 0 to 1 at each one independently.

REQUIRED OUTPUT
----------------
A tuple (max_count, begin_times):
  - max_count: an integer, the maximum number of simultaneously active
    meetings (0 if there are no meetings at all).
  - begin_times: a sorted list of the distinct timestamps at which the
    active-meeting count first (or, upon recurrence, again freshly)
    climbs to max_count.

ALGORITHM (sweep line over start/end events)
---------------------------------------------
1. Validate input: every interval must have start < end.
2. Build two kinds of events per meeting:
       (start, +1)   -- a meeting becomes active
       (end,   -1)   -- a meeting stops being active
3. Sort all events primarily by timestamp. For events sharing the same
   timestamp, process -1 (end) events strictly before +1 (start)
   events, since a meeting ending at t no longer counts as active at
   t, while a meeting starting at t does count as active at t.
4. Sweep through time in order of distinct timestamps. At each
   distinct timestamp, apply ALL deltas that occur at that timestamp
   at once (first the removals, then the additions) to get the new
   active count.
5. Track the running maximum count seen so far:
     - If the new count exceeds the running maximum, update the
       maximum and reset the list of "begin times" to just this
       timestamp.
     - If the new count equals the running maximum AND the count just
       increased to reach it at this timestamp (i.e. it was lower
       immediately before this timestamp's updates), record this
       timestamp as another "begin time".
     - Otherwise, do nothing.
6. Return the maximum count and the sorted list of begin times.
   (If there were no events at all -- the empty-input case -- return
   (0, []) immediately without sweeping.)

This runs in O(n log n) time due to sorting the 2n events, and O(n)
space, which is optimal for this class of interval-sweep problems.