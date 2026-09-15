"""
Matrix Rectangle Query
======================

Preprocesses an integer matrix so that repeated inclusive rectangle
queries can be answered for:
    - sum  : O(1) per query, via a 2D prefix-sum table
    - min  : O(area) per query, via direct rectangle scanning
    - max  : O(area) per query, via direct rectangle scanning

Standard library only. No randomness, no I/O, no network/APIs.
Deterministic: same matrix + same queries -> same results, always.
"""

from typing import List, Tuple, NamedTuple


class RectangleStats(NamedTuple):
    total: int
    minimum: int
    maximum: int


class MatrixRectQuery:
    """
    Preprocesses an R x C integer matrix for rectangle queries.

    Preprocessing:
        - prefix[i][j] = sum of all elements in rows [0, i-1], cols [0, j-1]
          (standard (R+1) x (C+1) inclusion-exclusion prefix-sum table)

    Query cost:
        - sum(r1, c1, r2, c2): O(1)
        - min_/max_(r1, c1, r2, c2): O((r2-r1+1) * (c2-c1+1))  (direct scan)
    """

    def __init__(self, matrix: List[List[int]]) -> None:
        if not matrix or not matrix[0]:
            raise ValueError("matrix must be non-empty and rectangular")

        row_len = len(matrix[0])
        for row in matrix:
            if len(row) != row_len:
                raise ValueError("all rows must have the same length")
            for v in row:
                if not isinstance(v, int):
                    raise TypeError("matrix must contain only integers")

        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = row_len

        # Build (rows+1) x (cols+1) prefix sum table.
        self.prefix = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for i in range(self.rows):
            row_running = 0
            for j in range(self.cols):
                row_running += matrix[i][j]
                self.prefix[i + 1][j + 1] = (
                    self.prefix[i][j + 1] + row_running
                )
        # Note: the above computes row-wise running sums then adds the
        # previous row's prefix; equivalent to the classic recurrence
        #   prefix[i+1][j+1] = prefix[i][j+1] + prefix[i+1][j] - prefix[i][j] + matrix[i][j]
        # but built via an explicit running sum per row for clarity.

    # ---- validation -----------------------------------------------------

    def _validate(self, r1: int, c1: int, r2: int, c2: int) -> None:
        if not (0 <= r1 <= r2 < self.rows):
            raise IndexError(
                f"invalid row range [{r1}, {r2}] for {self.rows} rows"
            )
        if not (0 <= c1 <= c2 < self.cols):
            raise IndexError(
                f"invalid col range [{c1}, {c2}] for {self.cols} cols"
            )

    # ---- queries ----------------------------------------------------------

    def sum_query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle sum in O(1)."""
        self._validate(r1, c1, r2, c2)
        P = self.prefix
        return (
            P[r2 + 1][c2 + 1]
            - P[r1][c2 + 1]
            - P[r2 + 1][c1]
            + P[r1][c1]
        )

    def min_query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle minimum via direct scan, O(area)."""
        self._validate(r1, c1, r2, c2)
        m = self.matrix
        best = m[r1][c1]
        for i in range(r1, r2 + 1):
            row = m[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                if v < best:
                    best = v
        return best

    def max_query(self, r1: int, c1: int, r2: int, c2: int) -> int:
        """Inclusive rectangle maximum via direct scan, O(area)."""
        self._validate(r1, c1, r2, c2)
        m = self.matrix
        best = m[r1][c1]
        for i in range(r1, r2 + 1):
            row = m[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                if v > best:
                    best = v
        return best

    def query(self, r1: int, c1: int, r2: int, c2: int) -> RectangleStats:
        """Convenience: sum, min, and max in one call (single scan for extrema)."""
        self._validate(r1, c1, r2, c2)
        total = self.sum_query(r1, c1, r2, c2)

        m = self.matrix
        lo = hi = m[r1][c1]
        for i in range(r1, r2 + 1):
            row = m[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                if v < lo:
                    lo = v
                elif v > hi:
                    hi = v
        return RectangleStats(total=total, minimum=lo, maximum=hi)


def _brute_force(
    matrix: List[List[int]], r1: int, c1: int, r2: int, c2: int
) -> RectangleStats:
    """Naive reference implementation used only for self-testing."""
    vals = [matrix[i][j] for i in range(r1, r2 + 1) for j in range(c1, c2 + 1)]
    return RectangleStats(total=sum(vals), minimum=min(vals), maximum=max(vals))


def _self_test() -> None:
    matrix = [
        [5, 2, -1, 4],
        [3, 8, 6, -2],
        [7, -3, 9, 1],
        [0, 4, 2, 10],
    ]
    mrq = MatrixRectQuery(matrix)

    queries: List[Tuple[int, int, int, int]] = [
        (0, 0, 0, 0),
        (0, 0, 3, 3),
        (1, 1, 2, 2),
        (0, 1, 2, 3),
        (3, 0, 3, 3),
        (0, 0, 2, 1),
    ]

    for (r1, c1, r2, c2) in queries:
        got = mrq.query(r1, c1, r2, c2)
        expected = _brute_force(matrix, r1, c1, r2, c2)
        assert got == expected, f"mismatch on {(r1, c1, r2, c2)}: {got} != {expected}"

    # Bad ranges must raise.
    try:
        mrq.query(2, 0, 1, 0)  # r1 > r2
        raise AssertionError("expected IndexError for invalid range")
    except IndexError:
        pass

    print("All self-tests passed.")
    print("Example query (0,0)-(3,3):", mrq.query(0, 0, 3, 3))
    print("Example query (1,1)-(2,2):", mrq.query(1, 1, 2, 2))


if __name__ == "__main__":
    _self_test()