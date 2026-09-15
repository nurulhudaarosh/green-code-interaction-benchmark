from typing import List, Tuple


class MatrixRangeQueryProcessor:
    """Preprocesses a 2D integer matrix for range sum, min, and max queries."""

    def __init__(self, matrix: List[List[int]]):
        """Builds a 2D prefix sum table for O(1) range sum queries.

        Args:
            matrix: A 2D list of integers of shape (R, C).
        """
        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = len(matrix[0]) if self.rows > 0 else 0

        # Build 1-based (R+1) x (C+1) prefix sum array
        self.prefix_sum = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for r in range(self.rows):
            for c in range(self.cols):
                self.prefix_sum[r + 1][c + 1] = (
                    matrix[r][c]
                    + self.prefix_sum[r][c + 1]
                    + self.prefix_sum[r + 1][c]
                    - self.prefix_sum[r][c]
                )

    def query(
        self, r1: int, c1: int, r2: int, c2: int
    ) -> Tuple[int, int, int]:
        """Answers range sum, min, and max for inclusive rectangle [r1..r2, c1..c2].

        Args:
            r1: Top-left row index.
            c1: Top-left column index.
            r2: Bottom-right row index.
            c2: Bottom-right column index.

        Returns:
            A tuple of (sum, min, max).
        """
        # 1. Calculate sum in O(1) via 2D prefix sum table
        rect_sum = (
            self.prefix_sum[r2 + 1][c2 + 1]
            - self.prefix_sum[r1][c2 + 1]
            - self.prefix_sum[r2 + 1][c1]
            + self.prefix_sum[r1][c1]
        )

        # 2. Calculate min and max via direct scanning
        rect_min = float("inf")
        rect_max = float("-inf")

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                val = self.matrix[r][c]
                if val < rect_min:
                    rect_min = val
                if val > rect_max:
                    rect_max = val

        return rect_sum, int(rect_min), int(rect_max)


# Example Usage & Test Verification
if __name__ == "__main__":
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    processor = MatrixRangeQueryProcessor(matrix)

    # Query full matrix (0, 0) to (2, 2)
    total_sum, min_val, max_val = processor.query(0, 0, 2, 2)
    print(f"Full Matrix -> Sum: {total_sum}, Min: {min_val}, Max: {max_val}")
    # Output: Full Matrix -> Sum: 45, Min: 1, Max: 9

    # Query subgrid from (1, 1) to (2, 2) -> [[5, 6], [8, 9]]
    sub_sum, sub_min, sub_max = processor.query(1, 1, 2, 2)
    print(f"Subgrid [1..2, 1..2] -> Sum: {sub_sum}, Min: {sub_min}, Max: {sub_max}")
    # Output: Subgrid [1..2, 1..2] -> Sum: 28, Min: 5, Max: 9