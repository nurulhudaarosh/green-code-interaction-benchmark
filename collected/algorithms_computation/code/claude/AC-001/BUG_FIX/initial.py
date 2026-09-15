Problem
-------
Given half-open meeting intervals [start, end), find:
  1. max_count  - the maximum number of meetings simultaneously active
                  at any instant.
  2. begin_times - the sorted, deduplicated list of times at which the
                  active-meeting count rises to reach that max_count.

Because intervals are half-open, a meeting ending at time t is no longer
counted as active at t, so it does not overlap with a meeting starting
at t.

Key constraints
----------------
- Each interval must satisfy start < end (half-open, non-empty).
- At a tied timestamp, end events are processed before start events,
  since a meeting freeing its slot at t must be resolved before a new
  meeting starting at t claims a slot.
- Output must be deterministic: same input -> same output every run
  (no dependence on set/dict iteration order, no randomness).
- begin_times records only *rises into* the max level, not every
  timestamp at which the max is merely sustained.

Required output
----------------
A tuple (max_count, begin_times) where begin_times is sorted ascending
with no duplicates.

Algorithm (sweep line)
-----------------------
1. Convert each interval (s, e) into two events: (s, +1) and (e, -1).
2. Sort events by (time, delta). Since -1 < +1, end events at a given
   timestamp naturally sort before start events at that same timestamp.
3. Sweep through events, grouping all events at an identical timestamp
   so they are applied atomically as one net change to the running count.
4. Whenever a timestamp's net effect increases the count:
     - if the new count exceeds the max seen so far, start a new
       begin_times list with this timestamp.
     - if the new count equals the current max, append this timestamp.
5. Non-increasing timestamps do not affect begin_times.

Complexity: O(n log n) for sorting, O(n) for the sweep.
Uses only the Python standard library; no network, APIs, randomness,
or human interaction.