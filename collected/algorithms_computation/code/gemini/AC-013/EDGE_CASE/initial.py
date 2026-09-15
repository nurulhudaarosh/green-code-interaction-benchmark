class MatrixRangeQuery:
    def __init__(self, matrix: list[list[int]]):
        """
        Preprocesses the matrix using a 2D prefix sum array for fast sum queries.
        """
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")

        self.rows = len(matrix)
        self.cols = len(matrix[0])
        self.matrix = matrix

        # Build 2D Prefix-Sum Table (1-indexed for convenience)
        self.prefix_sum = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for r in range(self.rows):
            row_accum = 0
            for c in range(self.cols):
                row_accum += matrix[r][c]
                self.prefix_sum[r + 1][c + 1] = self.prefix_sum[r][c + 1] + row_accum

    def query(self, r1: int, c1: int, r2: int, c2: int) -> tuple[int, int, int]:
        """
        Answers an inclusive subgrid query for (r1, c1) to (r2, c2).
        Returns a tuple: (sum, min, max)
        """
        # Validate boundary bounds
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise IndexError("Query coordinates out of matrix bounds.")

        # 1. Compute range sum in O(1) time
        rect_sum = (
            self.prefix_sum[r2 + 1][c2 + 1]
            - self.prefix_sum[r1][c2 + 1]
            - self.prefix_sum[r2 + 1][c1]
            + self.prefix_sum[r1][c1]
        )

        # 2. Compute minimum and maximum via direct scanning
        rect_min = float('inf')
        rect_max = float('-inf')

        for r in range(r1, r2 + 1):
            row_slice = self.matrix[r][c1 : c2 + 1]
            row_min = min(row_slice)
            row_max = max(row_slice)

            if row_min < rect_min:
                rect_min = row_min
            if row_max > rect_max:
                rect_max = row_max

        return int(rect_sum), int(rect_min), int(rect_max)


# Example usage / Verification
if __name__ == "__main__":
    grid = [
        [3, 0, 1, 4, 2],
        [5, 6, 3, 2, 1],
        [1, 2, 0, 1, 5],
        [4, 1, 0, 1, 7],
        [1, 0, 3, 0, 5]
    ]

    processor = MatrixRangeQuery(grid)

    # Query for subgrid (2, 1) to (4, 3)
    # Elements:
    # [2, 0, 1]
    # [1, 0, 1]
    # [0, 3, 0]
    # Sum: 8, Min: 0, Max: 3
    res_sum, res_min, res_max = processor.query(2, 1, 4, 3)
    print(f"Query (2,1) to (4,3) -> Sum: {res_sum}, Min: {res_min}, Max: {res_max}")