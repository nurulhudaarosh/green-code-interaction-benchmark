from typing import List, Tuple

class SubmatrixQuerySolver:
    def __init__(self, matrix: List[List[int]]):
        """
        Initializes the solver and constructs the 2D prefix sum table.
        Preprocessing Time Complexity: O(R * C)
        Space Complexity: O(R * C)
        """
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")
            
        self.matrix = matrix
        self.R = len(matrix)
        self.C = len(matrix[0])
        
        # Build 2D Prefix Sum Table (1-indexed for convenience)
        self.pref = [[0] * (self.C + 1) for _ in range(self.R + 1)]
        for r in range(1, self.R + 1):
            for c in range(1, self.C + 1):
                self.pref[r][c] = (
                    matrix[r - 1][c - 1]
                    + self.pref[r - 1][c]
                    + self.pref[r][c - 1]
                    - self.pref[r - 1][c - 1]
                )

    def query(self, r1: int, c1: int, r2: int, c2: int) -> Tuple[int, int, int]:
        """
        Answers an inclusive submatrix query for (sum, minimum, maximum).
        
        Parameters:
            r1, c1: Top-left coordinate (0-indexed)
            r2, c2: Bottom-right coordinate (0-indexed)
            
        Returns:
            Tuple[int, int, int]: (rectangle_sum, rectangle_min, rectangle_max)
        """
        # Validate coordinates
        if not (0 <= r1 <= r2 < self.R and 0 <= c1 <= c2 < self.C):
            raise IndexError("Query coordinates are out of matrix bounds.")

        # 1. Calculate sum in O(1) using 2D prefix sum formula
        total_sum = (
            self.pref[r2 + 1][c2 + 1]
            - self.pref[r1][c2 + 1]
            - self.pref[r2 + 1][c1]
            + self.pref[r1][c1]
        )

        # 2. Calculate minimum and maximum via direct scanning
        rect_min = self.matrix[r1][c1]
        rect_max = self.matrix[r1][c1]

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                val = self.matrix[r][c]
                if val < rect_min:
                    rect_min = val
                if val > rect_max:
                    rect_max = val

        return total_sum, rect_min, rect_max


# Example Usage & Verification
if __name__ == "__main__":
    grid = [
        [ 3,  0,  1,  4,  2],
        [ 5,  6,  3,  2,  1],
        [ 1,  2,  0,  1,  5],
        [ 4,  1,  0,  1,  7],
        [ 1,  0,  3,  0,  5]
    ]

    solver = SubmatrixQuerySolver(grid)

    # Example 1: Top-left submatrix (rows 2 to 3, cols 1 to 3)
    # Elements: 
    # [2, 0, 1]
    # [1, 0, 1]
    # Sum = 5, Min = 0, Max = 2
    r1, c1, r2, c2 = 2, 1, 3, 3
    s, mn, mx = solver.query(r1, c1, r2, c2)
    print(f"Query ({r1},{c1}) to ({r2},{c2}) -> Sum: {s}, Min: {mn}, Max: {mx}")

    # Example 2: Single element query at (0, 0)
    s, mn, mx = solver.query(0, 0, 0, 0)
    print(f"Query (0,0) to (0,0) -> Sum: {s}, Min: {mn}, Max: {mx}")