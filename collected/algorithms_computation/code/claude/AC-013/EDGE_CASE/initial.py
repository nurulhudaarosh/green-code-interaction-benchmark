"""
Matrix Range Query Processor
=============================

Preprocesses an integer matrix and answers inclusive rectangle queries for:
  - sum  : total of all elements in the rectangle
  - min  : smallest element in the rectangle
  - max  : largest element in the rectangle

Design:
  * Sum queries are backed by a 2D prefix-sum table built once in O(R*C),
    giving O(1) time per sum query.
  * Min/Max queries are answered by directly scanning the requested
    rectangle at query time (no auxiliary structure), giving
    O(rectangle area) time per query.

This intentionally mixes a precomputed fast path (sum) with an
on-demand scanning path (min/max) to model a workload where not every
operation is equally optimized.

Standard library only. No randomness, no I/O side effects beyond the
demo in __main__, no network/API access.
"""

from typing import List, Tuple


class MatrixRangeQueryError(ValueError):
    """Raised for malformed matrices or out-of-range / invalid queries."""


class MatrixRangeQuery:
    def __init__(self, matrix: List[List[int]]) -> None:
        if not matrix or not matrix[0]:
            raise MatrixRangeQueryError("Matrix must be non-empty.")

        num_cols = len(matrix[0])
        for row in matrix:
            if len(row) != num_cols:
                raise MatrixRangeQueryError("All rows must have equal length.")
            for value in row:
                if not isinstance(value, int):
                    raise MatrixRangeQueryError(
                        f"Matrix must contain only integers; got {value!r}."
                    )

        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = num_cols
        self.prefix = self._build_prefix_sums(matrix, self.rows, self.cols)

    @staticmethod
    def _build_prefix_sums(
        matrix: List[List[int]], rows: int, cols: int
    ) -> List[List[int]]:
        """Build an (rows+1) x (cols+1) prefix-sum table.

        prefix[i][j] = sum of matrix[0:i][0:j]  (top-left submatrix)
        """
        prefix = [[0] * (cols + 1) for _ in range(rows + 1)]
        for i in range(rows):
            row_sum = 0
            for j in range(cols):
                row_sum += matrix[i][j]
                prefix[i + 1][j + 1] = prefix[i][j + 1] + row_sum
        return prefix

    def _validate_rectangle(self, r1: int, c1: int, r2: int, c2: int) -> None:
        if not (0 <= r1 <= r2 < self.rows):
            raise MatrixRangeQueryError(
                f"Invalid row range ({r1}, {r2}) for matrix with {self.rows} rows."
            )
        if not (0 <= c1 <= c2 < self.cols):
            raise MatrixRangeQueryError(
                f"Invalid column range ({c1}, {c2}) for matrix with {self.cols} cols."
            )

    def sum_query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle sum in O(1) using the prefix-sum table."""
        self._validate_rectangle(r1, c1, r2, c2)
        p = self.prefix
        return (
            p[r2 + 1][c2 + 1]
            - p[r1][c2 + 1]
            - p[r2 + 1][c1]
            + p[r1][c1]
        )

    def min_query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle minimum via direct scan (no precomputation)."""
        self._validate_rectangle(r1, c1, r2, c2)
        m = self.matrix
        best = m[r1][c1]
        for i in range(r1, r2 + 1):
            row = m[i]
            for j in range(c1, c2 + 1):
                if row[j] < best:
                    best = row[j]
        return best

    def max_query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle maximum via direct scan (no precomputation)."""
        self._validate_rectangle(r1, c1, r2, c2)
        m = self.matrix
        best = m[r1][c1]
        for i in range(r1, r2 + 1):
            row = m[i]
            for j in range(c1, c2 + 1):
                if row[j] > best:
                    best = row[j]
        return best

    def query(self, kind: str, r1: int, c1: int, r2: int, c2: int) -> int:
        """Dispatch a single query by kind: 'sum', 'min', or 'max'."""
        dispatch = {
            "sum": self.sum_query,
            "min": self.min_query,
            "max": self.max_query,
        }
        try:
            fn = dispatch[kind]
        except KeyError as exc:
            raise MatrixRangeQueryError(
                f"Unknown query kind {kind!r}; expected one of {sorted(dispatch)}."
            ) from exc
        return fn(r1, c1, r2, c2)

    def batch_query(
        self, queries: List[Tuple[str, int, int, int, int]]
    ) -> List[int]:
        """Answer a list of (kind, r1, c1, r2, c2) queries, preserving order."""
        return [self.query(*q) for q in queries]


def _demo() -> None:
    matrix = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
    ]

    processor = MatrixRangeQuery(matrix)

    queries = [
        ("sum", 0, 0, 3, 3),  # whole matrix sum
        ("sum", 1, 1, 2, 2),  # inner 2x2 block: 6+7+10+11 = 34
        ("min", 0, 0, 3, 3),  # whole matrix min: 1
        ("max", 0, 0, 3, 3),  # whole matrix max: 16
        ("min", 2, 0, 3, 1),  # rows 2-3, cols 0-1: min(9,10,13,14) = 9
        ("max", 0, 2, 1, 3),  # rows 0-1, cols 2-3: max(3,4,7,8) = 8
        ("sum", 0, 0, 0, 0),  # single cell
    ]

    results = processor.batch_query(queries)

    print("Matrix:")
    for row in matrix:
        print(" ", row)
    print()
    print("Query results:")
    for (kind, r1, c1, r2, c2), result in zip(queries, results):
        print(f"  {kind}({r1},{c1})-({r2},{c2}) = {result}")


if __name__ == "__main__":
    _demo()