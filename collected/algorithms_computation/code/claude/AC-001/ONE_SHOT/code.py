Maximum concurrent meetings (sweep-line over half-open intervals [start, end)).

PROBLEM
-------
Given a list of meeting intervals [start, end) (end is exclusive — a meeting
that ends at time T does not overlap with one that starts at time T), find:
  1. The maximum number of meetings that are simultaneously active at any
     instant.
  2. The sorted list of distinct time points at which that maximum count is
     first reached (i.e., every timestamp where the active count rises to
     equal the global maximum).

KEY CONSTRAINTS
----------------
- Intervals are half-open: [start, end). A meeting is "active" on [start, end)
  and not active at or after 'end'.
- Because intervals are half-open, at a timestamp T where one meeting ends and
  another starts, they do NOT overlap. This means, when sweeping events at the
  same timestamp, all "end" events must be processed (i.e., counted as
  decrements) BEFORE any "start" events (increments) at that same timestamp.
- start < end is assumed for each meeting (zero/negative-length meetings are
  invalid and rejected).
- No use of randomness, network, external APIs, or human interaction —
  purely deterministic, standard-library computation.

REQUIRED OUTPUT
----------------
A tuple: (max_concurrent_count, sorted_list_of_timestamps_where_that_max_begins)

ALGORITHM (sweep line)
-----------------------
1. Convert each interval (s, e) into two events: a start event at time s and
   an end event at time e.
2. Sort all events by (time, kind), where "end" events are given a kind that
   sorts before "start" events at the same timestamp. This enforces the
   half-open semantics: same-instant ends are processed first.
3. Sweep through events in this order, maintaining a running `count` of
   active meetings. Process all events sharing the same timestamp together
   (all decrements for ends, then all increments for starts), then record
   the resulting count at that timestamp.
4. Track the global maximum count seen across the entire sweep.
5. Any timestamp whose post-processing count equals that global maximum is a
   time at which the maximum is "active/begins". Collect and sort those
   timestamps (they come out sorted naturally from the sweep, but we sort
   defensively).

Complexity: O(n log n) time for sorting 2n events, O(n) space.