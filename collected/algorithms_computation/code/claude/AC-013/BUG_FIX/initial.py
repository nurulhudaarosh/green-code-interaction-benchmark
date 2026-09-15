"""
Rectangle Query Processor
==========================

Preprocesses an integer matrix and answers inclusive rectangle queries for:
  - sum      -> O(1) per query, via a precomputed 2D prefix-sum table
  - minimum  -> O(area of rectangle) per query, via direct scanning
  - maximum  -> O(area of rectangle) per query, via direct scanning

Design rationale (mixed workload):
  Sums are needed frequently and cheaply via prefix sums (classic 2D
  cumulative sum trick). Extrema (min/max) are computed by direct
  rectangle scanning on each query rather than building an additional
  precomputed structure (e.g. sparse tables), keeping preprocessing
  O(R*C) while query cost for extrema scales with rectangle size.

Constraints:
  - The matrix must be non-empty and rectangular (all rows equal length).
  - Query coordinates are 0-indexed and inclusive: 0 <= r1 <= r2 < rows,
    0 <= c1 <= c2 < cols.
  - All matrix entries and query coordinates must be integers.

No randomness, no network access, no external dependencies:
  standard library only (this file uses nothing beyond built-ins).
"""

from typing import List, NamedTuple, Sequence, Tuple


class RectangleQueryError(ValueError):
    """Raised for invalid matrix input or out-of-range / malformed queries."""


class RectangleResult(NamedTuple):
    """Result of a single rectangle query."""
    r1: int
    c1: int
    r2: int
    c2: int
    total_sum: int
    minimum: int
    maximum: int


def _validate_matrix(matrix: Sequence[Sequence[int]]) -> Tuple[int, int]:
    """Validate that matrix is a non-empty rectangular grid of integers.

    Returns:
        (rows, cols)
    Raises:
        RectangleQueryError on any structural problem.
    """
    if matrix is None or len(matrix) == 0:
        raise RectangleQueryError("Matrix must be non-empty.")

    rows = len(matrix)
    cols = len(matrix[0])
    if cols == 0:
        raise RectangleQueryError("Matrix rows must be non-empty.")

    for row_index, row in enumerate(matrix):
        if len(row) != cols:
            raise RectangleQueryError(
                f"Matrix is not rectangular: row {row_index} has "
                f"{len(row)} columns, expected {cols}."
            )
        for col_index, value in enumerate(row):
            if not isinstance(value, int):
                raise RectangleQueryError(
                    f"Matrix entry at ({row_index}, {col_index}) is not "
                    f"an integer: {value!r}."
                )

    return rows, cols


class RectangleQueryProcessor:
    """Preprocesses a matrix and answers rectangle sum/min/max queries.

    Preprocessing:
        Builds a 2D prefix-sum table in O(rows * cols) time and space.
        Min/Max have no dedicated preprocessing structure by design;
        they are computed via direct scanning at query time.
    """

    def __init__(self, matrix: Sequence[Sequence[int]]):
        rows, cols = _validate_matrix(matrix)
        self._rows = rows
        self._cols = cols
        # Store an immutable-ish copy (list of tuples) to avoid external mutation.
        self._matrix: List[Tuple[int, ...]] = [tuple(row) for row in matrix]
        self._prefix_sum: List[List[int]] = self._build_prefix_sum(self._matrix, rows, cols)

    @staticmethod
    def _build_prefix_sum(
        matrix: Sequence[Sequence[int]], rows: int, cols: int
    ) -> List[List[int]]:
        """Build a (rows+1) x (cols+1) prefix-sum table.

        prefix[i][j] = sum of matrix[0..i-1][0..j-1] (top-left submatrix).
        """
        prefix = [[0] * (cols + 1) for _ in range(rows + 1)]
        for i in range(1, rows + 1):
            row_running = 0
            for j in range(1, cols + 1):
                row_running += matrix[i - 1][j - 1]
                prefix[i][j] = prefix[i - 1][j] + row_running
        return prefix

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    def _validate_query(self, r1: int, c1: int, r2: int, c2: int) -> None:
        for name, value in (("r1", r1), ("c1", c1), ("r2", r2), ("c2", c2)):
            if not isinstance(value, int):
                raise RectangleQueryError(f"Query coordinate {name} must be an integer, got {value!r}.")

        if not (0 <= r1 <= r2 < self._rows):
            raise RectangleQueryError(
                f"Invalid row range: r1={r1}, r2={r2} for matrix with {self._rows} rows."
            )
        if not (0 <= c1 <= c2 < self._cols):
            raise RectangleQueryError(
                f"Invalid column range: c1={c1}, c2={c2} for matrix with {self._cols} cols."
            )

    def query_sum(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle sum in O(1) using the prefix-sum table."""
        self._validate_query(r1, c1, r2, c2)
        p = self._prefix_sum
        return (
            p[r2 + 1][c2 + 1]
            - p[r1][c2 + 1]
            - p[r2 + 1][c1]
            + p[r1][c1]
        )

    def query_min_max(self, r1: int, c1: int, r2: int, c2: int) -> Tuple[int, int]:
        """Inclusive rectangle (min, max) via direct scanning: O(area)."""
        self._validate_query(r1, c1, r2, c2)
        matrix = self._matrix

        # Initialize from the first cell to avoid sentinel +/- infinity juggling.
        current_min = matrix[r1][c1]
        current_max = matrix[r1][c1]

        for i in range(r1, r2 + 1):
            row = matrix[i]
            for j in range(c1, c2 + 1):
                value = row[j]
                if value < current_min:
                    current_min = value
                if value > current_max:
                    current_max = value

        return current_min, current_max

    def query(self, r1: int, c1: int, r2: int, c2: int) -> RectangleResult:
        """Answer sum, min, and max for one inclusive rectangle query."""
        total_sum = self.query_sum(r1, c1, r2, c2)
        minimum, maximum = self.query_min_max(r1, c1, r2, c2)
        return RectangleResult(r1, c1, r2, c2, total_sum, minimum, maximum)

    def query_batch(
        self, queries: Sequence[Tuple[int, int, int, int]]
    ) -> List[RectangleResult]:
        """Answer a batch of queries, preserving input order."""
        return [self.query(*q) for q in queries]


def _format_result(result: RectangleResult) -> str:
    return (
        f"Rectangle ({result.r1},{result.c1}) -> ({result.r2},{result.c2}): "
        f"sum={result.total_sum}, min={result.minimum}, max={result.maximum}"
    )


def main() -> None:
    # Fixed, deterministic example matrix (no randomness).
    matrix = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
    ]

    processor = RectangleQueryProcessor(matrix)

    # Fixed set of deterministic queries: (r1, c1, r2, c2), inclusive.
    queries = [
        (0, 0, 0, 0),   # single cell
        (0, 0, 3, 3),   # entire matrix
        (1, 1, 2, 2),   # inner 2x2 block
        (0, 0, 1, 3),   # top two rows
        (2, 0, 3, 1),   # bottom-left 2x2 block
    ]

    results = processor.query_batch(queries)

    print("Matrix:")
    for row in matrix:
        print(" ", row)
    print()
    print("Query results:")
    for result in results:
        print(" ", _format_result(result))


if __name__ == "__main__":
    main()