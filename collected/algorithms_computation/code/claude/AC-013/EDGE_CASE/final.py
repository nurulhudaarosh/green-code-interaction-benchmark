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

Boundary notes:
  * The smallest permitted matrix is 1x1; its only valid query is the
    single cell (0,0,0,0), for all three query kinds.
  * A query rectangle can never be "empty" or "disconnected": the
    validated range 0 <= r1 <= r2 < R and 0 <= c1 <= c2 < C guarantees
    at least one contiguous, fully-connected cell is selected. There is
    therefore no tie-breaking ambiguity for min/max (a rectangle sum,
    minimum, and maximum are each a single well-defined value) and no
    empty-region case reachable via valid input; such inputs are
    rejected by validation instead of silently handled.

Standard library only. No randomness, no I/O side effects beyond the
demo/tests in __main__, no network/API access.
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


def _run_tests() -> None:
    # --- Smallest permitted input: 1x1 matrix ---
    single = MatrixRangeQuery([[42]])
    assert single.sum_query(0, 0, 0, 0) == 42
    assert single.min_query(0, 0, 0, 0) == 42
    assert single.max_query(0, 0, 0, 0) == 42
    assert single.batch_query(
        [("sum", 0, 0, 0, 0), ("min", 0, 0, 0, 0), ("max", 0, 0, 0, 0)]
    ) == [42, 42, 42]

    # 1x1 matrix: any range beyond the single cell is invalid, not "empty".
    for bad in [(0, 0, 1, 0), (0, 0, 0, 1), (-1, 0, 0, 0), (0, -1, 0, 0)]:
        try:
            single.sum_query(*bad)
            raise AssertionError(f"expected error for {bad}")
        except MatrixRangeQueryError:
            pass

    # --- Smallest permitted input: 1xN row vector ---
    row_vec = MatrixRangeQuery([[5, -3, 8, 0, -3]])
    assert row_vec.sum_query(0, 0, 0, 4) == 7
    assert row_vec.min_query(0, 0, 0, 4) == -3  # tie between two -3 cells
    assert row_vec.max_query(0, 0, 0, 4) == 8
    # Tie-breaking rule preserved: min/max return the value, not a position,
    # so duplicate extrema (-3 appears twice) do not create ambiguity.
    assert row_vec.min_query(0, 1, 0, 1) == -3
    assert row_vec.min_query(0, 4, 0, 4) == -3

    # --- Smallest permitted input: Nx1 column vector ---
    col_vec = MatrixRangeQuery([[1], [1], [1], [-2]])
    assert col_vec.sum_query(0, 0, 3, 0) == 1
    assert col_vec.min_query(0, 0, 3, 0) == -2
    assert col_vec.max_query(0, 0, 3, 0) == 1  # tie among three 1's

    # --- All-equal matrix: every extremum is a tie; value must still be
    #     deterministic and consistent regardless of scan order ---
    flat = MatrixRangeQuery([[7, 7], [7, 7]])
    assert flat.min_query(0, 0, 1, 1) == 7
    assert flat.max_query(0, 0, 1, 1) == 7
    assert flat.sum_query(0, 0, 1, 1) == 28

    # --- Negative numbers, mixed sign ---
    signed = MatrixRangeQuery([[-5, 3], [2, -1]])
    assert signed.sum_query(0, 0, 1, 1) == -1
    assert signed.min_query(0, 0, 1, 1) == -5
    assert signed.max_query(0, 0, 1, 1) == 3

    # --- "Disconnected-looking" queries are not permitted: only a single
    #     contiguous axis-aligned rectangle is a valid query shape. There
    #     is no valid syntax for a disconnected/multi-rectangle region, so
    #     we confirm the engine never silently accepts one by mis-specified
    #     bounds (e.g. r1 > r2, c1 > c2), which would implicitly describe
    #     an empty or invalid selection. ---
    grid = MatrixRangeQuery([[1, 2, 3], [4, 5, 6]])
    for bad in [(1, 0, 0, 0), (0, 2, 0, 1), (0, 0, 2, 0), (0, 0, 0, 3)]:
        try:
            grid.query("sum", *bad)
            raise AssertionError(f"expected error for {bad}")
        except MatrixRangeQueryError:
            pass

    # --- Malformed matrix construction: ragged rows, empty matrix, empty rows ---
    for bad_matrix in [[], [[]], [[1, 2], [3]]]:
        try:
            MatrixRangeQuery(bad_matrix)
            raise AssertionError(f"expected error for {bad_matrix}")
        except MatrixRangeQueryError:
            pass

    # --- Unknown query kind ---
    try:
        grid.query("median", 0, 0, 0, 0)
        raise AssertionError("expected error for unknown query kind")
    except MatrixRangeQueryError:
        pass

    # --- Full original demo output preserved exactly ---
    matrix = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16],
    ]
    processor = MatrixRangeQuery(matrix)
    queries = [
        ("sum", 0, 0, 3, 3),
        ("sum", 1, 1, 2, 2),
        ("min", 0, 0, 3, 3),
        ("max", 0, 0, 3, 3),
        ("min", 2, 0, 3, 1),
        ("max", 0, 2, 1, 3),
        ("sum", 0, 0, 0, 0),
    ]
    expected = [136, 34, 1, 16, 9, 8, 1]
    assert processor.batch_query(queries) == expected

    print("All tests passed.")


if __name__ == "__main__":
    _demo()
    print()
    _run_tests()