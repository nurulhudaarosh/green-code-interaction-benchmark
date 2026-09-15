"""
RECTANGLE STATISTICS ENGINE — edge-case hardened (smallest inputs, empty structures)
=====================================================================================

ORIGINAL PROBLEM (restated)
----------------------------
Given a static R x C integer matrix, preprocess it once, then answer many
inclusive rectangle queries (r1, c1, r2, c2) of type SUM, MIN, or MAX.

ORIGINAL REQUIRED OUTPUTS (unchanged)
--------------------------------------
- SUM answered in O(1) via a 2D prefix-sum table built during preprocessing.
- MIN/MAX answered by direct scanning of the requested rectangle at query
  time — no auxiliary min/max structure.
- Results are EXACT and DETERMINISTIC.
- TIE-BREAK CONTRACT (unchanged): MIN/MAX scans iterate rows then columns
  in increasing order, updating 'best' only on strict '<' (MIN) or strict
  '>' (MAX), so the first row-major occurrence of the extremal value is
  canonical. These operators must never become '<=' / '>='.
- Default call (include_summary=False) returns a plain int, exactly as
  before. When include_summary=True, an additional `operation_summary`
  dict is returned alongside the value, unchanged from the prior version.

NEWLY HANDLED EDGE CASES
--------------------------
1. SMALLEST PERMITTED INPUT:
   - A 1x1 matrix (single cell) is valid. Preprocessing builds a 2x2
     prefix table as normal; the only possible query is the single cell
     itself, and SUM/MIN/MAX must all equal that cell's value.
   - The smallest possible QUERY on any matrix is a 1x1 rectangle
     (r1 == r2 and c1 == c2). SUM/MIN/MAX must all equal matrix[r1][c1],
     with zero comparisons/updates performed for MIN/MAX (only the seed
     cell is inspected) and the fixed SUM operation count still applies.

2. EMPTY / DISCONNECTED STRUCTURES — WHERE ALLOWED:
   - The problem's domain is a rectangular grid queried by contiguous
     inclusive rectangles; there is no notion of a "disconnected"
     sub-region here (a query rectangle is always one contiguous block
     by definition), so disconnected-region support is explicitly
     OUT OF SCOPE and not silently accepted.
   - An EMPTY matrix (0 rows, or rows of length 0) is NOT a valid input
     per the original constraints (R,C >= 1) and continues to be
     explicitly rejected with a clear ValueError, rather than allowed
     to fail confusingly deeper in the code (e.g. IndexError on
     matrix[0]). This is preprocessing-time validation, not a new
     capability — it deterministically documents what "empty" means
     here (a data-entry error) rather than a supported degenerate case.
   - An EMPTY QUERY RECTANGLE (e.g. r2 < r1 or c2 < c1) is likewise
     invalid by the inclusive-bounds contract and continues to be
     rejected by _validate — there is no "vacuous" SUM/MIN/MAX defined
     for zero cells, so no empty-rectangle case is silently allowed.

All original fields, defaults, and tie-breaking behavior are unchanged.
Standard library only. No randomness, network access, or external services.
"""

from typing import List, Tuple, Dict, Union


QueryResultWithSummary = Tuple[int, Dict[str, int]]


class MatrixQueryEngine:
    def __init__(self, matrix: List[List[int]]):
        if not matrix or not matrix[0]:
            # Explicitly rejects the "empty structure" case: 0 rows, or
            # rows of length 0. This is a validation decision, not support
            # for empty matrices — R,C >= 1 is a hard input constraint.
            raise ValueError("Matrix must be non-empty (at least 1x1).")
        row_len = len(matrix[0])
        for row in matrix:
            if len(row) != row_len:
                raise ValueError("All rows must have the same length.")

        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = row_len

        # 2D prefix-sum table, 1-indexed for convenience. O(R*C) preprocessing.
        # Works unchanged for the smallest case (1x1 matrix -> 2x2 table).
        self.prefix = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for i in range(1, self.rows + 1):
            row_sum = 0
            for j in range(1, self.cols + 1):
                row_sum += matrix[i - 1][j - 1]
                self.prefix[i][j] = self.prefix[i - 1][j] + row_sum

    def _validate(self, r1: int, c1: int, r2: int, c2: int) -> None:
        # Rejects empty query rectangles (r2 < r1 or c2 < c1) and any
        # out-of-bounds rectangle. A single-cell rectangle (r1==r2, c1==c2)
        # is the smallest valid query and passes this check.
        if not (0 <= r1 <= r2 < self.rows):
            raise IndexError(f"Invalid row range: r1={r1}, r2={r2}")
        if not (0 <= c1 <= c2 < self.cols):
            raise IndexError(f"Invalid column range: c1={c1}, c2={c2}")

    # ------------------------------------------------------------------
    # SUM
    # ------------------------------------------------------------------
    def query_sum(
        self, r1: int, c1: int, r2: int, c2: int, include_summary: bool = False
    ) -> Union[int, QueryResultWithSummary]:
        """O(1) sum over inclusive rectangle using the prefix-sum table."""
        self._validate(r1, c1, r2, c2)
        P = self.prefix
        a = P[r2 + 1][c2 + 1]
        b = P[r1][c2 + 1]
        c = P[r2 + 1][c1]
        d = P[r1][c1]
        result = a - b - c + d  # fixed 3 arithmetic ops on 4 lookups, always

        if not include_summary:
            return result

        summary = {
            "lookups": 4,
            "arithmetic_ops": 3,
            "comparisons": 0,
            "total_operations": 7,
        }
        return result, summary

    # ------------------------------------------------------------------
    # MIN
    # ------------------------------------------------------------------
    def query_min(
        self, r1: int, c1: int, r2: int, c2: int, include_summary: bool = False
    ) -> Union[int, QueryResultWithSummary]:
        """
        Deterministic row-major direct scan for minimum.
        CONTRACT: rows then columns, strictly increasing order; update
        'best' only on strict '<'. Never change '<' to '<='.
        For a single-cell rectangle, only the seed cell is inspected and
        zero comparisons occur — the value is trivially that cell.
        """
        self._validate(r1, c1, r2, c2)
        best = self.matrix[r1][c1]
        cells_inspected = 0
        comparisons = 0
        updates = 0

        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                cells_inspected += 1
                if i == r1 and j == c1:
                    continue  # seed cell: no comparison against itself
                comparisons += 1
                if v < best:
                    best = v
                    updates += 1

        if not include_summary:
            return best

        summary = {
            "cells_inspected": cells_inspected,
            "comparisons": comparisons,
            "updates": updates,
            "total_operations": cells_inspected + comparisons,
        }
        return best, summary

    # ------------------------------------------------------------------
    # MAX
    # ------------------------------------------------------------------
    def query_max(
        self, r1: int, c1: int, r2: int, c2: int, include_summary: bool = False
    ) -> Union[int, QueryResultWithSummary]:
        """
        Deterministic row-major direct scan for maximum.
        Same contract as query_min: never change '>' to '>='.
        """
        self._validate(r1, c1, r2, c2)
        best = self.matrix[r1][c1]
        cells_inspected = 0
        comparisons = 0
        updates = 0

        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                cells_inspected += 1
                if i == r1 and j == c1:
                    continue
                comparisons += 1
                if v > best:
                    best = v
                    updates += 1

        if not include_summary:
            return best

        summary = {
            "cells_inspected": cells_inspected,
            "comparisons": comparisons,
            "updates": updates,
            "total_operations": cells_inspected + comparisons,
        }
        return best, summary

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    def query(
        self,
        kind: str,
        r1: int,
        c1: int,
        r2: int,
        c2: int,
        include_summary: bool = False,
    ) -> Union[int, QueryResultWithSummary]:
        """Dispatch a query by kind: 'SUM', 'MIN', or 'MAX'."""
        kind = kind.upper()
        if kind == "SUM":
            return self.query_sum(r1, c1, r2, c2, include_summary)
        elif kind == "MIN":
            return self.query_min(r1, c1, r2, c2, include_summary)
        elif kind == "MAX":
            return self.query_max(r1, c1, r2, c2, include_summary)
        else:
            raise ValueError(f"Unknown query kind: {kind}")

    def batch_query(
        self,
        queries: List[Tuple[str, int, int, int, int]],
        include_summary: bool = False,
    ) -> List[Union[int, QueryResultWithSummary]]:
        """Answer a deterministic, ordered list of queries."""
        return [
            self.query(kind, r1, c1, r2, c2, include_summary)
            for kind, r1, c1, r2, c2 in queries
        ]


def _brute_force(kind: str, matrix: List[List[int]], r1, c1, r2, c2) -> int:
    """Independent brute-force reference used only for self-verification."""
    vals = [matrix[i][j] for i in range(r1, r2 + 1) for j in range(c1, c2 + 1)]
    if kind == "SUM":
        return sum(vals)
    elif kind == "MIN":
        return min(vals)
    elif kind == "MAX":
        return max(vals)
    raise ValueError(kind)


def _regression_tests() -> None:
    """
    Verifies:
      1. Original behavior unchanged, including duplicate-extrema ties.
      2. operation_summary values correct and deterministic.
      3. NEW: smallest permitted input (1x1 matrix) behaves correctly.
      4. NEW: smallest permitted query (single-cell rectangle) on a
         larger matrix behaves correctly, including summary counts.
      5. NEW: empty/disconnected structures are explicitly and clearly
         rejected rather than silently mishandled.
    """
    matrix = [
        [5, 3],
        [3, 5],
    ]
    engine = MatrixQueryEngine(matrix)

    # --- Original behavior unchanged ---
    base_cases = [
        ("MIN", 0, 0, 1, 1, 3),
        ("MAX", 0, 0, 1, 1, 5),
        ("SUM", 0, 0, 1, 1, 16),
    ]
    for kind, r1, c1, r2, c2, expected in base_cases:
        result = engine.query(kind, r1, c1, r2, c2)
        assert isinstance(result, int)
        assert result == expected
        assert result == _brute_force(kind, matrix, r1, c1, r2, c2)

    # --- operation_summary unchanged ---
    sum_val, sum_summary = engine.query_sum(0, 0, 1, 1, include_summary=True)
    assert sum_val == 16
    assert sum_summary == {
        "lookups": 4,
        "arithmetic_ops": 3,
        "comparisons": 0,
        "total_operations": 7,
    }
    min_val, min_summary = engine.query_min(0, 0, 1, 1, include_summary=True)
    assert min_val == 3 and min_summary["cells_inspected"] == 4
    assert min_summary["comparisons"] == 3

    # --- NEW: smallest permitted input (1x1 matrix) ---
    tiny = MatrixQueryEngine([[42]])
    for kind in ("SUM", "MIN", "MAX"):
        v = tiny.query(kind, 0, 0, 0, 0)
        assert v == 42, f"1x1 matrix {kind} should be 42, got {v}"
    # With summaries: MIN/MAX must show zero comparisons/updates (only seed cell).
    v, s = tiny.query_min(0, 0, 0, 0, include_summary=True)
    assert v == 42
    assert s["cells_inspected"] == 1
    assert s["comparisons"] == 0
    assert s["updates"] == 0
    v, s = tiny.query_max(0, 0, 0, 0, include_summary=True)
    assert v == 42 and s["cells_inspected"] == 1 and s["comparisons"] == 0
    v, s = tiny.query_sum(0, 0, 0, 0, include_summary=True)
    assert v == 42 and s["total_operations"] == 7  # fixed cost, independent of size

    # --- NEW: smallest permitted query (single cell) on a larger matrix ---
    big = MatrixQueryEngine(
        [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
        ]
    )
    v, s = big.query_min(1, 1, 1, 1, include_summary=True)
    assert v == 5 and s["cells_inspected"] == 1 and s["comparisons"] == 0
    v, s = big.query_max(2, 0, 2, 0, include_summary=True)
    assert v == 7 and s["cells_inspected"] == 1 and s["comparisons"] == 0
    v = big.query("SUM", 0, 2, 0, 2)
    assert v == 3  # single cell sum equals the cell's own value

    # --- NEW: empty / disconnected structures explicitly rejected ---
    empty_cases_raised = 0
    for bad_matrix in ([], [[]]):
        try:
            MatrixQueryEngine(bad_matrix)
        except ValueError:
            empty_cases_raised += 1
    assert empty_cases_raised == 2, "Empty matrix inputs must raise ValueError."

    # An empty/inverted query rectangle must be rejected too (no vacuous result).
    try:
        big.query_sum(2, 2, 1, 1)  # r2 < r1: empty/invalid rectangle
        raised = False
    except IndexError:
        raised = True
    assert raised, "Inverted/empty query rectangle must raise IndexError."

    # Repeated calls remain deterministic.
    for _ in range(5):
        v2, s2 = engine.query_min(0, 0, 1, 1, include_summary=True)
        assert (v2, s2) == (min_val, min_summary)

    print("All regression tests passed (original behavior, summaries, and new edge cases).")


def main() -> None:
    matrix = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
    ]

    engine = MatrixQueryEngine(matrix)

    queries: List[Tuple[str, int, int, int, int]] = [
        ("SUM", 0, 0, 3, 3),
        ("SUM", 1, 1, 2, 2),
        ("MIN", 0, 0, 3, 3),
        ("MAX", 0, 0, 3, 3),
        ("MIN", 2, 0, 3, 1),
        ("MAX", 0, 2, 1, 3),
        ("SUM", 2, 2, 2, 2),
    ]

    print("Matrix:")
    for row in matrix:
        print(row)
    print()

    print("-- Default (include_summary=False), original behavior --")
    results = engine.batch_query(queries)
    for (kind, r1, c1, r2, c2), result in zip(queries, results):
        expected = _brute_force(kind, matrix, r1, c1, r2, c2)
        status = "OK" if result == expected else "MISMATCH"
        print(
            f"{kind:4s} rect=({r1},{c1})-({r2},{c2}) "
            f"-> result={result} expected={expected} [{status}]"
        )

    print("\n-- With operation_summary (include_summary=True) --")
    results_with_summary = engine.batch_query(queries, include_summary=True)
    for (kind, r1, c1, r2, c2), (value, summary) in zip(queries, results_with_summary):
        print(
            f"{kind:4s} rect=({r1},{c1})-({r2},{c2}) "
            f"-> value={value} operation_summary={summary}"
        )

    print("\n-- Smallest permitted input: 1x1 matrix --")
    tiny = MatrixQueryEngine([[42]])
    for kind in ("SUM", "MIN", "MAX"):
        print(f"{kind:4s} rect=(0,0)-(0,0) -> {tiny.query(kind, 0, 0, 0, 0)}")

    print()
    _regression_tests()


if __name__ == "__main__":
    main()