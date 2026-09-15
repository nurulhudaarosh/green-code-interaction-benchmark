from typing import List, Tuple, Optional


class RectangleStatisticsEngine:
    """Preprocess an integer matrix for sum/min/max rectangle queries.

    Contract:
      * sum  -> O(1) via 2D prefix sums.
      * min/max -> O(area) direct scan.
      * Deterministic tie handling: when several cells share the extremal
        value, the reported representative cell is the one with the smallest
        (row, col), independent of scan order. Values returned by `query`
        are always the extremal values themselves.
    """

    def __init__(self, matrix: List[List[int]]) -> None:
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        if any(len(row) != self.cols for row in matrix):
            raise ValueError("Matrix rows must all have the same length.")

        self.matrix = matrix
        self.prefix = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for i in range(self.rows):
            row_sum = 0
            pi = self.prefix[i]
            pi1 = self.prefix[i + 1]
            mi = matrix[i]
            for j in range(self.cols):
                row_sum += mi[j]
                pi1[j + 1] = pi[j + 1] + row_sum

    def _validate(self, r1: int, c1: int, r2: int, c2: int) -> None:
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise IndexError(
                f"Invalid rectangle ({r1},{c1})-({r2},{c2}) "
                f"for matrix {self.rows}x{self.cols}."
            )

    def rect_sum(self, r1: int, c1: int, r2: int, c2: int) -> int:
        self._validate(r1, c1, r2, c2)
        P = self.prefix
        return P[r2 + 1][c2 + 1] - P[r1][c2 + 1] - P[r2 + 1][c1] + P[r1][c1]

    def rect_min_with_cell(self, r1: int, c1: int, r2: int, c2: int
                           ) -> Tuple[int, Tuple[int, int]]:
        """Deterministic: among ties, return the smallest (row, col)."""
        self._validate(r1, c1, r2, c2)
        best: Optional[Tuple[int, int, int]] = None  # (value, row, col)
        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                cand = (row[j], i, j)
                if best is None or cand < best:
                    best = cand
        v, i, j = best  # type: ignore[misc]
        return v, (i, j)

    def rect_max_with_cell(self, r1: int, c1: int, r2: int, c2: int
                           ) -> Tuple[int, Tuple[int, int]]:
        """Deterministic: among ties, return the smallest (row, col)."""
        self._validate(r1, c1, r2, c2)
        best: Optional[Tuple[int, int, int]] = None  # (-value, row, col)
        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                cand = (-row[j], i, j)
                if best is None or cand < best:
                    best = cand
        neg_v, i, j = best  # type: ignore[misc]
        return -neg_v, (i, j)

    def rect_min(self, r1: int, c1: int, r2: int, c2: int) -> int:
        return self.rect_min_with_cell(r1, c1, r2, c2)[0]

    def rect_max(self, r1: int, c1: int, r2: int, c2: int) -> int:
        return self.rect_max_with_cell(r1, c1, r2, c2)[0]

    def query(self, r1: int, c1: int, r2: int, c2: int) -> Tuple[int, int, int]:
        """Public contract: (sum, min, max)."""
        return (
            self.rect_sum(r1, c1, r2, c2),
            self.rect_min(r1, c1, r2, c2),
            self.rect_max(r1, c1, r2, c2),
        )

    def query_full(self, r1: int, c1: int, r2: int, c2: int):
        """Extended contract exposing the deterministic tie-break cells."""
        s = self.rect_sum(r1, c1, r2, c2)
        mn, mn_cell = self.rect_min_with_cell(r1, c1, r2, c2)
        mx, mx_cell = self.rect_max_with_cell(r1, c1, r2, c2)
        return s, (mn, mn_cell), (mx, mx_cell)


def _demo() -> None:
    M = [[5, 1, 5],
         [1, 5, 1],
         [5, 1, 5]]
    eng = RectangleStatisticsEngine(M)

    # Values unchanged for the core contract.
    assert eng.query(0, 0, 2, 2) == (27, 1, 5)
    assert eng.query(0, 0, 0, 0) == (5, 5, 5)
    assert eng.query(1, 0, 1, 2) == (7, 1, 5)

    # Deterministic tie-break: min=1 -> smallest (row,col) is (0,1);
    # max=5 -> smallest (row,col) is (0,0).
    assert eng.query_full(0, 0, 2, 2) == (27, (1, (0, 1)), (5, (0, 0)))

    # Order-independence: recompute with reversed scan order and compare.
    def scan_min_rev(r1, c1, r2, c2):
        best = None
        for i in range(r2, r1 - 1, -1):
            for j in range(c2, c1 - 1, -1):
                cand = (M[i][j], i, j)
                if best is None or cand < best:
                    best = cand
        return best[0], (best[1], best[2])

    def scan_max_rev(r1, c1, r2, c2):
        best = None
        for i in range(r2, r1 - 1, -1):
            for j in range(c2, c1 - 1, -1):
                cand = (-M[i][j], i, j)
                if best is None or cand < best:
                    best = cand
        return -best[0], (best[1], best[2])

    for r1 in range(3):
        for c1 in range(3):
            for r2 in range(r1, 3):
                for c2 in range(c1, 3):
                    _, mn_cell = eng.rect_min_with_cell(r1, c1, r2, c2)
                    _, mx_cell = eng.rect_max_with_cell(r1, c1, r2, c2)
                    assert mn_cell == scan_min_rev(r1, c1, r2, c2)[1]
                    assert mx_cell == scan_max_rev(r1, c1, r2, c2)[1]

    print("All checks passed (deterministic tie handling verified).")


if __name__ == "__main__":
    _demo()