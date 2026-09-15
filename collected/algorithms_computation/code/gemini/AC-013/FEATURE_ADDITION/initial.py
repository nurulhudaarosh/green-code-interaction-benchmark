class MatrixRangeQueryProcessor:
    def __init__(self, matrix: list[list[int]]):
        """Preprocesses the matrix using a 2D prefix-sum table for range sum queries."""
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")

        self.R = len(matrix)
        self.C = len(matrix[0])
        self.matrix = matrix

        # Construct 2D prefix sum table (sized (R+1) x (C+1))
        self.prefix = [[0] * (self.C + 1) for _ in range(self.R + 1)]
        for r in range(self.R):
            row_sum = 0
            for c in range(self.C):
                row_sum += matrix[r][c]
                self.prefix[r + 1][c + 1] = self.prefix[r][c + 1] + row_sum

    def query(self, r1: int, c1: int, r2: int, c2: int) -> tuple[int, int, int]:
        """
        Answers inclusive rectangle query for (r1, c1) to (r2, c2).
        Returns a tuple: (sum, min, max)
        """
        # Boundary validation
        if not (0 <= r1 <= r2 < self.R and 0 <= c1 <= c2 < self.C):
            raise IndexError("Rectangle coordinates are out of matrix bounds.")

        # O(1) Range Sum lookup
        rect_sum = (
            self.prefix[r2 + 1][c2 + 1]
            - self.prefix[r1][c2 + 1]
            - self.prefix[r2 + 1][c1]
            + self.prefix[r1][c1]
        )

        # Direct scanning for min and max over subgrid rows
        rect_min = float('inf')
        rect_max = float('-inf')

        for r in range(r1, r2 + 1):
            row_slice = self.matrix[r][c1:c2 + 1]
            row_min = min(row_slice)
            row_max = max(row_slice)
            if row_min < rect_min:
                rect_min = row_min
            if row_max > rect_max:
                rect_max = row_max

        return rect_sum, int(rect_min), int(rect_max)


# Example Usage & Verification
if __name__ == "__main__":
    grid = [
        [3,  1,  4,  1,  5],
        [9,  2,  6,  5,  3],
        [5,  8,  9,  7,  9],
        [8,  4,  6,  2,  6]
    ]

    processor = MatrixRangeQueryProcessor(grid)

    # Query for rectangle top-left (1, 1) to bottom-right (2, 3)
    # Target region:
    # [2, 6, 5]
    # [8, 9, 7]
    r1, c1, r2, c2 = 1, 1, 2, 3
    total, minimum, maximum = processor.query(r1, c1, r2, c2)

    print(f"Query ({r1},{c1}) to ({r2},{c2}):")
    print(f"Sum: {total} (Expected: 37)")
    print(f"Min: {minimum} (Expected: 2)")
    print(f"Max: {maximum} (Expected: 9)")