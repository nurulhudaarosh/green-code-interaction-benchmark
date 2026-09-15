from typing import List, Tuple


class RectangleAggregator:
    """Preprocesses an integer matrix for sum/min/max rectangle queries."""

    def __init__(self, matrix: List[List[int]]) -> None:
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        if any(len(row) != self.cols for row in matrix):
            raise ValueError("Matrix rows must all have the same length.")

        self.matrix = matrix
        # 2D prefix sum table with (rows+1) x (cols+1) shape.
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
        return (
            P[r2 + 1][c2 + 1]
            - P[r1][c2 + 1]
            - P[r2 + 1][c1]
            + P[r1][c1]
        )

    def rect_min(self, r1: int, c1: int, r2: int, c2: int) -> int:
        self._validate(r1, c1, r2, c2)
        best = None
        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                if best is None or v < best:
                    best = v
        return best  # type: ignore[return-value]

    def rect_max(self, r1: int, c1: int, r2: int, c2: int) -> int:
        self._validate(r1, c1, r2, c2)
        best = None
        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                v = row[j]
                if best is None or v > best:
                    best = v
        return best  # type: ignore[return-value]

    def query(self, r1: int, c1: int, r2: int, c2: int) -> Tuple[int, int, int]:
        """Return (sum, min, max) for the inclusive rectangle."""
        return (
            self.rect_sum(r1, c1, r2, c2),
            self.rect_min(r1, c1, r2, c2),
            self.rect_max(r1, c1, r2, c2),
        )


def _demo() -> None:
    matrix = [
        [3, -1, 4, 1],
        [5,  9, 2, 6],
        [0, -7, 8, 3],
    ]
    ra = RectangleAggregator(matrix)

    # Whole matrix: sum = 33, min = -7, max = 9
    assert ra.query(0, 0, 2, 3) == (33, -7, 9)

    # Top-left 2x2: [3,-1;5,9] -> sum 16, min -1, max 9
    assert ra.query(0, 0, 1, 1) == (16, -1, 9)

    # Middle column rows 0..2: [-1, 9, -7] -> sum 1, min -7, max 9
    assert ra.query(0, 1, 2, 1) == (1, -7, 9)

    # Single cell
    assert ra.query(2, 1, 2, 1) == (-7, -7, -7)

    # Bottom-right 2x2: [2,6;8,3] -> sum 19, min 2, max 8
    assert ra.query(1, 2, 2, 3) == (19, 2, 8)

    # Brute-force cross-check on random (deterministic) sub-rectangles
    for r1 in range(3):
        for c1 in range(4):
            for r2 in range(r1, 3):
                for c2 in range(c1, 4):
                    flat = [
                        matrix[i][j]
                        for i in range(r1, r2 + 1)
                        for j in range(c1, c2 + 1)
                    ]
                    expected = (sum(flat), min(flat), max(flat))
                    got = ra.query(r1, c1, r2, c2)
                    assert got == expected, (r1, c1, r2, c2, got, expected)

    print("All checks passed.")


if __name__ == "__main__":
    _demo()