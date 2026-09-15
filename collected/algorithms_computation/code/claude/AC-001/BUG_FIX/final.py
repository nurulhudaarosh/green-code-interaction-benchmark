Interval Conflict Analyzer
===========================

Problem
-------
Given half-open meeting intervals [start, end), find:
  1. max_count   - the maximum number of meetings simultaneously active
                    at any instant.
  2. begin_times - the sorted, deduplicated list of times at which the
                    active-meeting count rises to reach that max_count.

Because intervals are half-open, a meeting ending at time t is no longer
counted as active at t, so it does not overlap with a meeting starting
at t.

Key constraints
----------------
- Each interval must satisfy start < end (half-open, non-empty).
- At a tied timestamp, END events must be processed before START events.
  This must be guaranteed by the sort key itself, not by input order,
  so the result is deterministic regardless of how intervals are listed.
- begin_times records only *rises into* the max level, not every
  timestamp at which the max is merely sustained.

Required output
----------------
(max_count, begin_times), with begin_times sorted ascending, no duplicates.

Algorithm (sweep line)
-----------------------
1. Convert each interval (s, e) into two events: (s, +1) and (e, -1).
2. Sort events by the key (time, delta). Since -1 < +1, this places all
   end events at a given timestamp before all start events at that same
   timestamp -- independent of input order (fixes the reported defect).
3. Sweep through events, grouping all events at an identical timestamp
   so they are applied atomically as one net change to the running count.
4. Whenever a timestamp's net effect increases the count:
     - if the new count exceeds the max seen so far, start a new
       begin_times list with this timestamp.
     - if the new count equals the current max, append this timestamp.
5. Non-increasing timestamps do not affect begin_times.

Complexity: O(n log n) sort, O(n) sweep.
Standard library only; no network, APIs, randomness, or human interaction.