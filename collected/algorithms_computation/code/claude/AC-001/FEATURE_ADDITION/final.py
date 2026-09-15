Interval Conflict Analyzer
===========================================

RESTATED PROBLEM
-----------------
Given a collection of half-open meeting intervals [start, end), determine:
  1. The maximum number of meetings that are simultaneously active at any
     single point in time.
  2. The sorted list of distinct time points at which that maximum count
     is first reached (each time the active count transitions UP into
     the maximum level — including cases where it dips below the maximum
     and later climbs back up to it again).

Because intervals are half-open, a meeting ending at time t and another
meeting starting at time t do NOT overlap (the first meeting has already
vacated the slot by time t).

KEY CONSTRAINTS (unchanged)
-----------------------------
- Intervals are half-open: [start, end), and a valid interval requires
  start < end. Degenerate/invalid intervals (start >= end) are skipped.
- Tie-breaking rule at equal timestamps: an "end" event at time t must be
  processed BEFORE a "start" event at time t, since the departing meeting
  no longer occupies time t.
- Solution must be deterministic: no randomness, no wall-clock time, no
  network/API calls, no human interaction — pure function of the input.
- Only the Python standard library may be used.

REQUIRED OUTPUTS (original — unchanged when the new feature is disabled)
--------------------------------------------------------------------------
A tuple: (max_count: int, begin_times: List[float/int])
where begin_times is sorted ascending and contains each timestamp at
which the running active-meeting count rises to reach max_count.

This original two-field output is preserved exactly, with the exact same
field order, types, and semantics, whenever the new feature described
below is not requested (i.e., the default call signature/behavior is
100% backward compatible).

NEW FEATURE — `operation_summary`
------------------------------------
When explicitly requested (via `include_operation_summary=True`), the
function additionally returns a third field, `operation_summary`, which
is a deterministic report of the number of major computational
decisions/operations performed by the sweep-line algorithm on the given
input. This is useful for auditing algorithmic cost, verifying scaling
behavior, or teaching how the sweep-line technique works internally.

`operation_summary` is a dict with the following integer counters:
  - "events_created"        : number of (time, type, delta) events built
                                from the input intervals (2 per valid
                                interval: one start, one end).
  - "intervals_skipped"     : number of invalid/degenerate intervals
                                skipped (start >= end).
  - "sort_comparisons_key"  : number of events sorted (proxy for the
                                sort operation performed; Python's sort
                                is deterministic/Timsort under the hood).
  - "timestamp_merge_steps" : number of individual events folded into
                                grouped (time, net_delta) records during
                                the collapse-by-timestamp step.
  - "distinct_timestamps"   : number of distinct timestamps produced
                                after merging.
  - "sweep_pass_1_steps"    : number of decision steps (one per distinct
                                timestamp) taken while computing the
                                global maximum concurrent count.
  - "sweep_pass_2_steps"    : number of decision steps (one per distinct
                                timestamp) taken while detecting "rise
                                into max" begin points.
  - "begin_points_detected" : number of timestamps identified as valid
                                begin points for the maximum.
  - "total_major_operations": sum of all the above counters — a single
                                deterministic scalar summarizing overall
                                algorithmic work performed.

When `include_operation_summary=False` (the default), the function
returns exactly the original 2-tuple, with no behavior change of any
kind — every original field and requirement remains unchanged.

ALGORITHM (Sweep-Line) — unchanged
-------------------------------------
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
   ascending order since we process events chronologically), plus,
   optionally, the `operation_summary` described above.

Time complexity: O(n log n) for sorting; O(n) for the two sweeps and the
operation-counting instrumentation (all instrumentation is O(1) extra
work per existing step, so overall complexity is unchanged).
Space complexity: O(n).