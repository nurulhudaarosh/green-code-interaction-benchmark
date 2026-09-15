"""
RECTANGLE STATISTICS ENGINE — with optional operation_summary feature
========================================================================

ORIGINAL PROBLEM (restated)
----------------------------
Given a static R x C integer matrix, preprocess it once, then answer many
inclusive rectangle queries (r1, c1, r2, c2) of type SUM, MIN, or MAX.

ORIGINAL REQUIRED OUTPUTS (unchanged)
--------------------------------------
- SUM answered in O(1) via a 2D prefix-sum table built during preprocessing.
- MIN/MAX answered by direct scanning of the requested rectangle at query
  time — no auxiliary min/max structure (sparse table, segment tree, etc.).
- Results must be EXACT and DETERMINISTIC: for a fixed matrix and fixed
  rectangle, MIN/MAX must always return the same value.
- TIE-BREAK CONTRACT (unchanged): MIN/MAX scans iterate rows then columns
  in increasing order, updating 'best' only on strict '<' (MIN) or strict
  '>' (MAX), so the first row-major occurrence of the extremal value is
  canonical. These operators must never become '<=' / '>='.
- By default, query()/batch_query() return exactly the numeric result
  (an int) for each query — this default behavior is UNCHANGED.

NEW FEATURE (opt-in, additive only)
-------------------------------------
Each query method now accepts an optional `include_summary: bool = False`
parameter. When True (or when using `query_with_summary` / `batch_query`
with `include_summary=True`), the call additionally returns an
`operation_summary` field: a small deterministic dict reporting the number
of major computational decisions/operations the algorithm performed to
answer that specific query:

  - SUM: the prefix-sum inclusion-exclusion formula always performs a
    fixed, deterministic number of operations regardless of rectangle
    size: 4 table lookups and 3 arithmetic combinations (2 subtractions,
    1 addition) => operation_summary = {"lookups": 4, "arithmetic_ops": 3,
    "comparisons": 0, "total_operations": 7}.
  - MIN/MAX: each cell visited during the scan is one "candidate
    inspection", and each strict comparison against `best` is one
    "comparison"; the summary reports both, plus how many times `best`
    was actually updated (deterministic tie-break: only strict
    improvements count).

When `include_summary` is False (the default), every original method's
return value and signature-relevant behavior is exactly as before: a
plain int. Nothing about the disabled path changes.

Standard library only. No randomness, network access, or external services.
"""

from typing import List, Tuple, Dict, Union


# A query result when include_summary=True: (value, operation_summary)
QueryResultWithSummary = Tuple[int, Dict[str, int]]


class MatrixQueryEngine:
    def __init__(self, matrix: List[List[int]]):
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")
        row_len = len(matrix[0])
        for row in matrix:
            if len(row) != row_len:
                raise ValueError("All rows must have the same length.")

        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = row_len

        # 2D prefix-sum table, 1-indexed for convenience. O(R*C) preprocessing.
        self.prefix = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for i in range(1, self.rows + 1):
            row_sum = 0
            for j in range(1, self.cols + 1):
                row_sum += matrix[i - 1][j - 1]
                self.prefix[i][j] = self.prefix[i - 1][j] + row_sum

    def _validate(self, r1: int, c1: int, r2: int, c2: int) -> None:
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
        """O(1) sum over inclusive rectangle using the prefix-sum table.
        Default behavior (include_summary=False) is unchanged: returns int.
        """
        self._validate(r1, c1, r2, c2)
        P = self.prefix
        a = P[r2 + 1][c2 + 1]
        b = P[r1][c2 + 1]
        c = P[r2 + 1][c1]
        d = P[r1][c1]
        result = a - b - c + d  # 3 arithmetic ops on 4 lookups, always

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
        Default behavior (include_summary=False) is unchanged: returns int.
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
                    # seed cell: no comparison performed against itself
                    continue
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
        Default behavior (include_summary=False) is unchanged: returns int.
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
        """Dispatch a query by kind: 'SUM', 'MIN', or 'MAX'.
        Default behavior (include_summary=False) is exactly the original:
        returns a plain int.
        """
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
        """Answer a deterministic, ordered list of queries.
        Default behavior (include_summary=False) is exactly the original:
        returns a list of plain ints.
        """
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
      1. Original behavior (include_summary=False) is unchanged, including
         duplicate-extrema tie handling.
      2. New operation_summary values are correct and deterministic.
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
        result = engine.query(kind, r1, c1, r2, c2)  # include_summary defaults False
        assert isinstance(result, int), "Default query() must return a plain int."
        assert result == expected
        assert result == _brute_force(kind, matrix, r1, c1, r2, c2)

    # --- New feature: operation_summary ---
    sum_val, sum_summary = engine.query_sum(0, 0, 1, 1, include_summary=True)
    assert sum_val == 16
    assert sum_summary == {
        "lookups": 4,
        "arithmetic_ops": 3,
        "comparisons": 0,
        "total_operations": 7,
    }

    min_val, min_summary = engine.query_min(0, 0, 1, 1, include_summary=True)
    assert min_val == 3
    assert min_summary["cells_inspected"] == 4  # 2x2 rectangle
    assert min_summary["comparisons"] == 3  # all but the seed cell
    assert min_summary["total_operations"] == min_summary["cells_inspected"] + min_summary["comparisons"]

    max_val, max_summary = engine.query_max(0, 0, 1, 1, include_summary=True)
    assert max_val == 5
    assert max_summary["cells_inspected"] == 4
    assert max_summary["comparisons"] == 3

    # Repeated calls must be deterministic (identical value and summary).
    for _ in range(5):
        v2, s2 = engine.query_min(0, 0, 1, 1, include_summary=True)
        assert (v2, s2) == (min_val, min_summary)

    print("All regression tests passed (original behavior + operation_summary).")


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

    # Default behavior: unchanged, plain int results.
    print("-- Default (include_summary=False), original behavior --")
    results = engine.batch_query(queries)
    for (kind, r1, c1, r2, c2), result in zip(queries, results):
        expected = _brute_force(kind, matrix, r1, c1, r2, c2)
        status = "OK" if result == expected else "MISMATCH"
        print(
            f"{kind:4s} rect=({r1},{c1})-({r2},{c2}) "
            f"-> result={result} expected={expected} [{status}]"
        )

    # New feature: with operation_summary.
    print("\n-- With operation_summary (include_summary=True) --")
    results_with_summary = engine.batch_query(queries, include_summary=True)
    for (kind, r1, c1, r2, c2), (value, summary) in zip(queries, results_with_summary):
        print(
            f"{kind:4s} rect=({r1},{c1})-({r2},{c2}) "
            f"-> value={value} operation_summary={summary}"
        )

    print()
    _regression_tests()


if __name__ == "__main__":
    main()