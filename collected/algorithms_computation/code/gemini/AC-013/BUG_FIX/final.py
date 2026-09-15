from typing import List, Tuple


class RectangleStatisticsEngine:
    """Preprocesses a 2D integer matrix to answer inclusive rectangle queries

    for sum (via 2D prefix-sum) and min/max (via direct scanning).
    """

    def __init__(self, matrix: List[List[int]]):
        """Initializes the engine and builds the 2D prefix-sum table.

        Args:
            matrix: Non-empty 2D grid of integers.

        Raises:
            ValueError: If the matrix is empty or non-rectangular.
        """
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty and 2-dimensional.")

        self.rows = len(matrix)
        self.cols = len(matrix[0])

        if any(len(row) != self.cols for row in matrix):
            raise ValueError("All rows in the matrix must have equal length.")

        self.matrix = matrix

        # Build 1-based (rows + 1) x (cols + 1) prefix sum table
        self.prefix_sum = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for r in range(self.rows):
            for c in range(self.cols):
                self.prefix_sum[r + 1][c + 1] = (
                    int(matrix[r][c])
                    + self.prefix_sum[r][c + 1]
                    + self.prefix_sum[r + 1][c]
                    - self.prefix_sum[r][c]
                )

    def query(
        self, r1: int, c1: int, r2: int, c2: int
    ) -> Tuple[int, int, int]:
        """Answers inclusive subgrid query [r1..r2, c1..c2].

        Args:
            r1: Top row index.
            c1: Left column index.
            r2: Bottom row index.
            c2: Right column index.

        Returns:
            Tuple of (sum, minimum, maximum) strictly as integers.

        Raises:
            ValueError: If coordinates form an invalid range (r1 > r2 or c1 > c2).
            IndexError: If coordinates are out of matrix bounds.
        """
        # Enforce valid coordinate ordering
        if r1 > r2 or c1 > c2:
            raise ValueError(
                f"Invalid subgrid bounds: r1 ({r1}) > r2 ({r2}) or c1 ({c1}) > c2 ({c2})."
            )

        # Enforce matrix boundary limits
        if not (0 <= r1 < self.rows and 0 <= r2 < self.rows):
            raise IndexError(
                f"Row indices [{r1}, {r2}] out of bounds for matrix with {self.rows} rows."
            )
        if not (0 <= c1 < self.cols and 0 <= c2 < self.cols):
            raise IndexError(
                f"Column indices [{c1}, {c2}] out of bounds for matrix with {self.cols} columns."
            )

        # 1. Exact O(1) Range Sum via inclusion-exclusion on 2D Prefix Sum array
        rect_sum = (
            self.prefix_sum[r2 + 1][c2 + 1]
            - self.prefix_sum[r1][c2 + 1]
            - self.prefix_sum[r2 + 1][c1]
            + self.prefix_sum[r1][c1]
        )

        # 2. Direct scanning for extrema initialized to exact matrix values (no floats)
        rect_min = self.matrix[r1][c1]
        rect_max = self.matrix[r1][c1]

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                val = self.matrix[r][c]
                if val < rect_min:
                    rect_min = val
                if val > rect_max:
                    rect_max = val

        return rect_sum, rect_min, rect_max


# Self-contained verification suite
if __name__ == "__main__":
    grid = [[10, -2, 3], [4, 15, 6], [7, 8, 9]]
    engine = RectangleStatisticsEngine(grid)

    # Valid Query: Top-Left (0,0) to Bottom-Right (1,1) -> [[10, -2], [4, 15]]
    s, mn, mx = engine.query(0, 0, 1, 1)
    print(f"Query Result -> Sum: {s}, Min: {mn}, Max: {mx}")
    assert (s, mn, mx) == (27, -2, 15)

    # Verify bound exception handling
    try:
        engine.query(1, 1, 0, 0)
    except ValueError as e:
        print(f"Successfully caught invalid query bounds: {e}")