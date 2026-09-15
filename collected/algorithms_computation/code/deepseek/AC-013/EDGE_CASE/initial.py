from typing import List, Tuple


class RectangleQueryProcessor:
    def __init__(self, matrix: List[List[int]]):
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty")

        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = len(matrix[0])

        # Validate rectangular shape
        for r in range(self.rows):
            if len(matrix[r]) != self.cols:
                raise ValueError("Matrix must be rectangular")

        # Build 2D prefix sum table with 1-based indexing
        # pref[i][j] = sum of matrix[0..i-1][0..j-1]
        self.pref = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]

        for i in range(1, self.rows + 1):
            row_sum = 0
            for j in range(1, self.cols + 1):
                row_sum += self.matrix[i - 1][j - 1]
                self.pref[i][j] = self.pref[i - 1][j] + row_sum

    def query(self, r1: int, c1: int, r2: int, c2: int) -> Tuple[int, int, int]:
        """
        Returns (sum, minimum, maximum) for inclusive rectangle
        from (r1, c1) to (r2, c2).
        """
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise IndexError("Query rectangle is out of bounds")

        # O(1) sum using prefix table
        total = (
            self.pref[r2 + 1][c2 + 1]
            - self.pref[r1][c2 + 1]
            - self.pref[r2 + 1][c1]
            + self.pref[r1][c1]
        )

        # Direct scan for min and max
        mn = None
        mx = None

        for r in range(r1, r2 + 1):
            row = self.matrix[r]
            for c in range(c1, c2 + 1):
                val = row[c]
                if mn is None or val < mn:
                    mn = val
                if mx is None or val > mx:
                    mx = val

        return total, mn, mx


def main():
    matrix = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
    ]

    processor = RectangleQueryProcessor(matrix)

    queries = [
        (0, 0, 0, 0),   # single cell
        (0, 0, 1, 1),   # top-left 2x2
        (1, 1, 2, 2),   # bottom-right 2x2
        (0, 0, 2, 3),   # whole matrix
        (0, 1, 2, 2),   # middle columns
    ]

    for q in queries:
        r1, c1, r2, c2 = q
        result = processor.query(r1, c1, r2, c2)
        print(f"Query {q}: sum={result[0]}, min={result[1]}, max={result[2]}")


if __name__ == "__main__":
    main()