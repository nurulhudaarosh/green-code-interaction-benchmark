"""
Weighted Job Scheduling — Problem Restatement, Bug Report, and Fix
====================================================================

PROBLEM (restated)
-------------------
Given jobs, each with (start, finish, profit), select a subset of jobs such
that no two selected jobs overlap in time, maximizing total profit. Two jobs
are compatible ("non-overlapping") if one finishes at or before the other
starts — jobs that merely touch at a shared endpoint ARE allowed together.

EXPECTED BEHAVIOR
------------------
- Compute the maximum total profit achievable by any compatible subset.
- Among *all* subsets that achieve that maximum profit, return exactly the
  one result required by the spec: the subset whose ORIGINAL 0-based indices,
  sorted increasing, form the lexicographically smallest index sequence of
  any other max-profit subset's sorted index sequence.
- The method must be: sort by finish time, binary-search compatible
  predecessors, and use dynamic programming.

BUG REPORT
----------
Rule violated: "Return exactly the required result with deterministic tie
handling; use Sort by finish time, binary-search compatible predecessors,
and use dynamic programming."

The earlier implementation stored, at each DP position i, a SINGLE
representative state `(profit, sorted_index_tuple)` — the locally
lexicographically smallest tuple among the two immediate candidates
("exclude job i" vs "include job i + best predecessor state"). This is
unsound: comparing two tuples of *possibly different length* in isolation
and keeping only the smaller one can permanently discard a tuple that,
after a LATER job's original index is inserted into it, would have produced
the true lexicographically smallest overall answer. Local optimality of the
tie-break does not imply global optimality once more elements get appended.

DEFECT DEMONSTRATION (small, valid example)
--------------------------------------------
    index 0: (start=0, finish=1, profit=10)
    index 1: (start=1, finish=2, profit=0)   # touches index 0, compatible
    index 2: (start=2, finish=3, profit=5)   # touches index 1, compatible

All three jobs are mutually compatible (each only touches the next at an
endpoint), so every subset is feasible. The maximum total profit is 15,
achieved by exactly two subsets:
    {0, 2}    -> profit 10 + 5 = 15   (index sequence (0, 2))
    {0, 1, 2} -> profit 10 + 0 + 5 = 15   (index sequence (0, 1, 2))

Comparing (0, 2) and (0, 1, 2) element-by-element: index 0 matches (0 == 0),
index 1 differs (2 vs 1), and 1 < 2 — so (0, 1, 2) is the lexicographically
smaller sequence and is the ONLY correct answer.

The buggy DP, however, compares the *prefix* states (0,) vs (0, 1) after
processing just indices {0, 1} (both give profit 10, since job 1 contributes
0), and — using only local information — keeps (0,) because a tuple that is
a strict prefix of another compares smaller in isolation. That candidate,
(0, 1), is discarded forever. When job 2 is folded in afterward, the
algorithm can only build on the surviving (0,) state, producing (0, 2) as
its final answer.

    buggy result : (15, [0, 2])         <-- WRONG index sequence
    correct      : (15, [0, 1, 2])      <-- required by the tie-break rule

Both have the correct maximum profit (15), so a profit-only check would miss
this defect entirely — it is specifically a tie-break/determinism bug.

FIX
---
The DP is still built on "sort by finish time, binary-search compatible
predecessors" — that part was already correct and is kept unchanged for
computing the maximum profit value. What changes is how the exact set of
indices is reconstructed:

1. Run the standard forward DP (sort by finish, bisect predecessors, DP on
   profit only) to get MAXP, the true maximum total profit. No tie-break
   bookkeeping is done here, so this step cannot be wrong.
2. Reconstruct the answer index-by-index, in increasing ORIGINAL index order
   (0, 1, 2, ..., n-1), using a standard, provably correct exchange
   argument for "lexicographically smallest optimum":
     - Maintain the set of already-accepted intervals (kept sorted by start
       time, since original-index order need not match chronological
       order -- a later-considered job may need to slot into an earlier
       time gap than an already-accepted job).
     - For each original index i in increasing order:
         * If job i overlaps anything already accepted, it cannot be
           included -- skip it.
         * Otherwise, compute (again via sort + bisect + DP -- the same
           method) the maximum achievable profit from the remaining jobs
           (original index > i) that would still be individually
           compatible with the accepted set if job i were added to it. If
           `fixed_profit + profit_i + that value` equals MAXP exactly, job
           i CAN be part of a maximum-profit completion, so we greedily
           commit to including it (this is always at least as good for
           lexicographic minimality as skipping it, since including a
           smaller index can never make the sorted tuple larger).
           Otherwise, including it would make the maximum unreachable, so
           it must be excluded.
   This never needs to reconsider a decision once made, runs the same
   sort/bisect/DP subroutine at each step, and is easy to prove correct by
   induction: at every step the invariant "the remaining jobs can still
   reach exactly the required remaining profit" is maintained exactly.

This preserves every unrelated requirement (touching endpoints allowed,
same output format, standard library only, fully deterministic, no
randomness/network/human interaction) and fixes only the tie-break defect.
"""

from bisect import bisect_right, bisect_left
from typing import List, Optional, Tuple


def _max_profit(jobs: List[Tuple[int, int, int]]) -> int:
    """
    Standard weighted job scheduling DP: sort by finish time, binary-search
    the latest compatible predecessor, and run a profit-only DP. Returns just
    the maximum achievable total profit for the given job list (no index
    bookkeeping — this subroutine is intentionally simple and provably
    correct on its own).
    """
    if not jobs:
        return 0
    ordered = sorted(jobs, key=lambda j: j[1])  # sort by finish time
    finishes = [j[1] for j in ordered]
    n = len(ordered)
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        start, finish, profit = ordered[i - 1]
        # latest predecessor with finish <= start (touching endpoints OK)
        pred = bisect_right(finishes, start, 0, i - 1) - 1
        dp[i] = max(dp[i - 1], profit + dp[pred + 1])
    return dp[n]


def schedule_jobs(jobs: List[Tuple[int, int, int]]) -> Tuple[int, List[int]]:
    """
    Solve the weighted job scheduling problem.

    Parameters
    ----------
    jobs : list of (start, finish, profit) tuples.

    Returns
    -------
    (max_profit, selected_indices)
        max_profit: the maximum achievable total profit.
        selected_indices: sorted list of original 0-based indices forming the
        lexicographically-smallest maximum-profit solution.
    """
    n = len(jobs)
    if n == 0:
        return 0, []

    for idx, (s, f, _p) in enumerate(jobs):
        if s > f:
            raise ValueError(f"Job {idx} has start > finish: ({s}, {f})")

    max_profit = _max_profit(jobs)

    # Jobs are considered in ORIGINAL index order (needed for the lex-min
    # tie-break), which does NOT generally match chronological (start-time)
    # order. So "compatible with what's accepted so far" cannot be tracked
    # with a single last-finish scalar -- a later-considered job may need to
    # slot into an earlier gap in time than an already-accepted job. Instead
    # we keep the accepted set as two lists, sorted by start time, and use
    # binary search to check compatibility against both neighbors.
    accepted_starts: List[int] = []
    accepted_finishes: List[int] = []

    def fits(s: int, f: int) -> Optional[int]:
        """Return the insertion position if (s, f) doesn't overlap any
        currently accepted interval, else None."""
        pos = bisect_left(accepted_starts, s)
        if pos > 0 and accepted_finishes[pos - 1] > s:
            return None  # overlaps the accepted interval just before it
        if pos < len(accepted_starts) and accepted_starts[pos] < f:
            return None  # overlaps the accepted interval just after it
        return pos

    selected: List[int] = []
    fixed_profit = 0

    for i in range(n):
        start, finish, profit = jobs[i]
        pos = fits(start, finish)
        if pos is None:
            continue  # incompatible with what's already accepted

        required_after = max_profit - fixed_profit - profit
        if required_after < 0:
            continue  # cannot possibly reach the required total

        # Tentatively insert job i into the accepted set, then find which
        # later original indices would still be individually compatible
        # with that (hypothetical) accepted set.
        temp_starts = accepted_starts[:pos] + [start] + accepted_starts[pos:]
        temp_finishes = accepted_finishes[:pos] + [finish] + accepted_finishes[pos:]

        pool = []
        for k in range(i + 1, n):
            ks, kf, _kp = jobs[k]
            kpos = bisect_left(temp_starts, ks)
            overlaps = (kpos > 0 and temp_finishes[kpos - 1] > ks) or (
                kpos < len(temp_starts) and temp_starts[kpos] < kf
            )
            if not overlaps:
                pool.append(jobs[k])

        achievable = _max_profit(pool)

        if achievable == required_after:
            selected.append(i)
            fixed_profit += profit
            accepted_starts, accepted_finishes = temp_starts, temp_finishes
        # else: including job i would make the maximum unreachable -> skip

    assert fixed_profit == max_profit  # internal consistency guarantee
    return max_profit, selected


def _self_check() -> None:
    """Regression tests, including the defect demonstrated above."""

    # --- The defect-triggering example: fixed now returns the lexicographically
    # smallest of the two tied maximum-profit index sequences. ---
    jobs = [(0, 1, 10), (1, 2, 0), (2, 3, 5)]
    profit, chosen = schedule_jobs(jobs)
    assert (profit, chosen) == (15, [0, 1, 2]), (profit, chosen)

    # Simple non-overlapping set, unique optimum.
    profit, chosen = schedule_jobs([(1, 3, 5), (3, 5, 6), (0, 6, 4)])
    assert (profit, chosen) == (11, [0, 1]), (profit, chosen)

    # Touching endpoints are compatible.
    profit, chosen = schedule_jobs([(1, 4, 3), (4, 6, 2)])
    assert (profit, chosen) == (5, [0, 1]), (profit, chosen)

    # Classic weighted interval scheduling example.
    jobs = [(1, 2, 50), (3, 5, 20), (6, 19, 100), (2, 100, 200)]
    profit, chosen = schedule_jobs(jobs)
    assert (profit, chosen) == (250, [0, 3]), (profit, chosen)

    # Two disjoint equal-profit jobs beat one overlapping alternative.
    jobs = [(0, 1, 10), (2, 3, 10), (0, 3, 10)]
    profit, chosen = schedule_jobs(jobs)
    assert (profit, chosen) == (20, [0, 1]), (profit, chosen)

    # Three mutually compatible jobs: take all of them.
    jobs = [(5, 10, 10), (0, 3, 10), (20, 30, 10)]
    profit, chosen = schedule_jobs(jobs)
    assert (profit, chosen) == (30, [0, 1, 2]), (profit, chosen)

    # Genuine index-order tie: {0,2} and {1,2} both give profit 15;
    # [0, 2] is lexicographically smaller.
    jobs = [(0, 5, 10), (1, 6, 10), (10, 15, 5)]
    profit, chosen = schedule_jobs(jobs)
    assert (profit, chosen) == (15, [0, 2]), (profit, chosen)

    # Original index order does NOT match chronological order: index 0 is
    # (5,10), index 1 is (0,3) which occurs earlier in time, index 2 is
    # (20,30). All three are mutually compatible and must all be selected.
    jobs = [(5, 10, 10), (0, 3, 10), (20, 30, 10)]
    profit, chosen = schedule_jobs(jobs)
    assert (profit, chosen) == (30, [0, 1, 2]), (profit, chosen)

    print("All self-checks passed (including the defect regression test).")


if __name__ == "__main__":
    _self_check()

    print("\nDefect demonstration")
    print("---------------------")
    demo_jobs = [(0, 1, 10), (1, 2, 0), (2, 3, 5)]
    print(f"Jobs: {demo_jobs}")
    print("Old (buggy) result : (15, [0, 2])   <- wrong tie-break")
    print(f"Fixed result       : {schedule_jobs(demo_jobs)}   <- correct")