class MatrixRangeQueryProcessor:
    def __init__(self, grid: list[list[int]]):
        """Preprocesses the input matrix for range queries."""
        if not grid or not grid[0]:
            raise ValueError("Grid must be a non-empty 2D list of integers.")
            
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        
        # Build 2D Prefix Sum Table with 1-based indexing
        self.prefix_sum = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        
        for r in range(self.rows):
            for c in range(self.cols):
                self.prefix_sum[r + 1][c + 1] = (
                    grid[r][c]
                    + self.prefix_sum[r][c + 1]
                    + self.prefix_sum[r + 1][c]
                    - self.prefix_sum[r][c]
                )

    def query(self, r1: int, c1: int, r2: int, c2: int) -> tuple[int, int, int]:
        """
        Answers inclusive rectangle queries for (Sum, Minimum, Maximum).
        
        Coordinates must satisfy: 0 <= r1 <= r2 < R and 0 <= c1 <= c2 < C
        """
        # Validate boundary inputs
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise IndexError("Query coordinates are out of matrix bounds.")

        # O(1) Range Sum calculation using 2D Prefix Sum
        rect_sum = (
            self.prefix_sum[r2 + 1][c2 + 1]
            - self.prefix_sum[r1][c2 + 1]
            - self.prefix_sum[r2 + 1][c1]
            + self.prefix_sum[r1][c1]
        )

        # O(area) Direct scanning for Minimum and Maximum
        rect_min = float('inf')
        rect_max = float('-inf')

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                val = self.grid[r][c]
                if val < rect_min:
                    rect_min = val
                if val > rect_max:
                    rect_max = val

        return rect_sum, rect_min, rect_max


# --- Example Usage ---
if __name__ == "__main__":
    matrix = [
        [3,  0,  1,  4,  2],
        [5,  6,  3,  2,  1],
        [1,  2,  0,  1,  5],
        [4,  1,  0,  1,  7],
        [1,  0,  3,  0,  5]
    ]

    processor = MatrixRangeQueryProcessor(matrix)
    
    # Query region: r1=2, c1=1 to r2=4, c2=3
    # Elements:
    # [2, 0, 1]
    # [1, 0, 1]
    # [0, 3, 0]
    total_sum, min_val, max_val = processor.query(2, 1, 4, 3)
    
    print(f"Subgrid Sum: {total_sum}")  # Output: 8
    print(f"Subgrid Min: {min_val}")    # Output: 0
    print(f"Subgrid Max: {max_val}")    # Output: 3