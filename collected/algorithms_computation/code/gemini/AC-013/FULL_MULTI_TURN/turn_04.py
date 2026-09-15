from typing import List, Tuple, Dict, Any, Union

class RectangleStatisticsEngine:
    """
    Pre-processes an integer matrix to answer submatrix queries for 
    sum, minimum, maximum, and optional operational statistics summaries.
    """
    def __init__(self, matrix: List[List[int]]):
        if not matrix or not isinstance(matrix, list) or len(matrix) == 0:
            raise ValueError("Input matrix must be a non-empty 2D list.")
            
        if not matrix[0] or not isinstance(matrix[0], list) or len(matrix[0]) == 0:
            raise ValueError("Input matrix rows must be non-empty.")
            
        self.matrix = matrix
        self.R = len(matrix)
        self.C = len(matrix[0])
        
        # Verify uniform row lengths (disconnected structural check)
        for row_idx, row in enumerate(matrix):
            if not isinstance(row, list):
                raise ValueError(f"Row at index {row_idx} is not a valid list.")
            if len(row) != self.C:
                raise ValueError(f"Non-rectangular matrix structure: row {row_idx} has length {len(row)}, expected {self.C}.")
        
        # Build 2D Prefix Sum Table (1-indexed prefix array)
        self.pref = [[0] * (self.C + 1) for _ in range(self.R + 1)]
        for r in range(1, self.R + 1):
            for c in range(1, self.C + 1):
                self.pref[r][c] = (
                    self.matrix[r - 1][c - 1]
                    + self.pref[r - 1][c]
                    + self.pref[r][c - 1]
                    - self.pref[r - 1][c - 1]
                )

    def query(
        self, 
        r1: int, 
        c1: int, 
        r2: int, 
        c2: int, 
        include_summary: bool = False
    ) -> Union[Tuple[int, int, int], Tuple[int, int, int, Dict[str, int]]]:
        """
        Executes inclusive range query for rectangle defined by (r1, c1) to (r2, c2).
        
        Returns:
            Default (include_summary=False): 
                Tuple[int, int, int] -> (rect_sum, rect_min, rect_max)
            Extended (include_summary=True): 
                Tuple[int, int, int, Dict[str, int]] -> (rect_sum, rect_min, rect_max, operation_summary)
        """
        # Coordinate boundary validations
        if not (0 <= r1 < self.R and 0 <= r2 < self.R and 0 <= c1 < self.C and 0 <= c2 < self.C):
            raise IndexError(f"Query coordinates ({r1}, {c1}), ({r2}, {c2}) are out of grid bounds ({self.R}x{self.C}).")
            
        if r1 > r2 or c1 > c2:
            raise ValueError(f"Invalid query bounds: top-left ({r1}, {c1}) must be <= bottom-right ({r2}, {c2}).")

        # 1. Sum query via 2D Prefix Sum Table - O(1)
        rect_sum = (
            self.pref[r2 + 1][c2 + 1]
            - self.pref[r1][c2 + 1]
            - self.pref[r2 + 1][c1]
            + self.pref[r1][c1]
        )

        # 2. Extrema query via deterministic row-major direct scanning - O(H * W)
        rect_min = self.matrix[r1][c1]
        rect_max = self.matrix[r1][c1]

        scanned_cells = 0
        extrema_comparisons = 0
        min_updates = 0
        max_updates = 0

        # Deterministic row-major scan (top-to-bottom, left-to-right)
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                val = self.matrix[r][c]
                scanned_cells += 1

                extrema_comparisons += 1
                if val < rect_min:
                    rect_min = val
                    min_updates += 1

                extrema_comparisons += 1
                if val > rect_max:
                    rect_max = val
                    max_updates += 1

        if include_summary:
            summary = {
                "prefix_sum_lookups": 4,
                "scanned_cells": scanned_cells,
                "extrema_comparisons": extrema_comparisons,
                "min_updates": min_updates,
                "max_updates": max_updates,
            }
            return rect_sum, rect_min, rect_max, summary

        return rect_sum, rect_min, rect_max


# ==========================================
# TEST SUITE
# ==========================================
def run_tests():
    print("Running test suite...")

    # Test 1: Smallest Permitted Input (1x1 matrix)
    engine_1x1 = RectangleStatisticsEngine([[42]])
    res_1x1 = engine_1x1.query(0, 0, 0, 0, include_summary=True)
    assert res_1x1[0] == 42 and res_1x1[1] == 42 and res_1x1[2] == 42
    assert res_1x1[3]["scanned_cells"] == 1
    assert res_1x1[3]["min_updates"] == 0 and res_1x1[3]["max_updates"] == 0
    print("[PASS] Test 1: Smallest Permitted Input (1x1)")

    # Test 2: Empty Grid / Row Rejection
    try:
        RectangleStatisticsEngine([])
        assert False, "Should have raised ValueError on empty outer matrix"
    except ValueError:
        print("[PASS] Test 2a: Rejects empty outer grid []")

    try:
        RectangleStatisticsEngine([[]])
        assert False, "Should have raised ValueError on empty inner row"
    except ValueError:
        print("[PASS] Test 2b: Rejects empty row grid [[]]")

    # Test 3: Disconnected / Non-Uniform Structure Rejection
    try:
        RectangleStatisticsEngine([[1, 2, 3], [4, 5]])
        assert False, "Should have raised ValueError on jagged/non-uniform matrix"
    except ValueError:
        print("[PASS] Test 3: Rejects disconnected/jagged matrix")

    # Test 4: Single Column (N x 1) and Single Row (1 x N) Grids
    col_engine = RectangleStatisticsEngine([[5], [10], [-3], [7]])
    assert col_engine.query(1, 0, 3, 0) == (14, -3, 10)
    print("[PASS] Test 4a: Single-column grid query")

    row_engine = RectangleStatisticsEngine([[8, -1, 4, 12, 0]])
    assert row_engine.query(0, 1, 0, 3) == (15, -1, 12)
    print("[PASS] Test 4b: Single-row grid query")

    # Test 5: Deterministic Tie-Handling Validation
    # All duplicate values: min_updates and max_updates should be 0 since first cell sets initial running values
    dup_engine = RectangleStatisticsEngine([[7, 7], [7, 7]])
    s, mn, mx, summary = dup_engine.query(0, 0, 1, 1, include_summary=True)
    assert (s, mn, mx) == (28, 7, 7)
    assert summary["scanned_cells"] == 4
    assert summary["min_updates"] == 0
    assert summary["max_updates"] == 0
    print("[PASS] Test 5: Deterministic tie-handling (duplicate entries)")

    # Test 6: Boundary & Invalid Range Violations
    standard_engine = RectangleStatisticsEngine([[1, 2], [3, 4]])
    try:
        standard_engine.query(1, 0, 0, 0) # r1 > r2
        assert False, "Should have raised ValueError for inverted coordinates"
    except ValueError:
        print("[PASS] Test 6a: Rejects inverted range bounds (r1 > r2)")

    try:
        standard_engine.query(0, 0, 5, 1) # Out of bounds index
        assert False, "Should have raised IndexError for out-of-bounds coordinates"
    except IndexError:
        print("[PASS] Test 6b: Rejects out-of-bounds index")

    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    run_tests()