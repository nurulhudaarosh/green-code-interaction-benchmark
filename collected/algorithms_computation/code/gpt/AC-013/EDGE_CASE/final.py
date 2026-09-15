from typing import List, Tuple, Dict


def rectangle_statistics(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]]
) -> List[Dict[str, int]]:
    """
    Rectangle Statistics Engine.

    Each query is (r1, c1, r2, c2), with inclusive boundaries.

    Returns, for each query:
        {
            "sum": rectangle sum,
            "min": rectangle minimum,
            "max": rectangle maximum
        }

    Algorithm:
      - 2D prefix-sum table for O(1) rectangle sums.
      - Direct scanning for minimum and maximum.
    """

    # Empty matrix is allowed only when there are no queries.
    if not matrix:
        if queries:
            raise ValueError("Cannot query an empty matrix.")
        return []

    # An empty first row means the matrix has no usable columns.
    if not matrix[0]:
        if queries:
            raise ValueError("Cannot query an empty matrix.")
        return []

    rows = len(matrix)
    cols = len(matrix[0])

    # Matrix must be rectangular.
    for row in matrix:
        if len(row) != cols:
            raise ValueError("Matrix must be rectangular.")

    # ---------------------------------------------------------
    # Build 2D prefix-sum table.
    # prefix[r][c] represents the sum of the rectangle
    # from (0, 0) through (r-1, c-1).
    # ---------------------------------------------------------
    prefix = [[0] * (cols + 1) for _ in range(rows + 1)]

    for r in range(1, rows + 1):
        row_sum = 0

        for c in range(1, cols + 1):
            row_sum += matrix[r - 1][c - 1]

            prefix[r][c] = (
                prefix[r - 1][c] + row_sum
            )

    results = []

    # ---------------------------------------------------------
    # Process queries.
    # ---------------------------------------------------------
    for r1, c1, r2, c2 in queries:

        # Validate inclusive coordinates.
        if not (
            0 <= r1 <= r2 < rows
            and
            0 <= c1 <= c2 < cols
        ):
            raise ValueError(
                f"Invalid rectangle query: {(r1, c1, r2, c2)}"
            )

        # Prefix-table boundaries.
        top = r1
        left = c1
        bottom = r2 + 1
        right = c2 + 1

        # O(1) rectangle sum.
        rectangle_sum = (
            prefix[bottom][right]
            - prefix[top][right]
            - prefix[bottom][left]
            + prefix[top][left]
        )

        # Direct scan for extrema.
        minimum = matrix[r1][c1]
        maximum = matrix[r1][c1]

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                value = matrix[r][c]

                if value < minimum:
                    minimum = value

                if value > maximum:
                    maximum = value

        results.append({
            "sum": rectangle_sum,
            "min": minimum,
            "max": maximum
        })

    return results


# =============================================================
# Tests
# =============================================================

def run_tests():
    # ---------------------------------------------------------
    # Test 1: Smallest permitted input: 1x1 matrix.
    # ---------------------------------------------------------
    matrix = [[7]]
    queries = [(0, 0, 0, 0)]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 7, "min": 7, "max": 7}
    ]

    # ---------------------------------------------------------
    # Test 2: Smallest matrix with an empty query list.
    # ---------------------------------------------------------
    assert rectangle_statistics([[42]], []) == []

    # ---------------------------------------------------------
    # Test 3: Empty matrix with no queries.
    # This is the allowed empty structure.
    # ---------------------------------------------------------
    assert rectangle_statistics([], []) == []

    # ---------------------------------------------------------
    # Test 4: Single row.
    # ---------------------------------------------------------
    matrix = [[-3, 5, 2, -8]]

    queries = [
        (0, 0, 0, 0),
        (0, 1, 0, 3),
        (0, 0, 0, 3)
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": -3, "min": -3, "max": -3},
        {"sum": -1, "min": -8, "max": 5},
        {"sum": -4, "min": -8, "max": 5}
    ]

    # ---------------------------------------------------------
    # Test 5: Single column.
    # ---------------------------------------------------------
    matrix = [
        [4],
        [-2],
        [9],
        [1]
    ]

    queries = [
        (0, 0, 3, 0),
        (1, 0, 2, 0),
        (2, 0, 2, 0)
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 12, "min": -2, "max": 9},
        {"sum": 7, "min": -2, "max": 9},
        {"sum": 9, "min": 9, "max": 9}
    ]

    # ---------------------------------------------------------
    # Test 6: All values equal.
    # ---------------------------------------------------------
    matrix = [
        [5, 5],
        [5, 5]
    ]

    queries = [
        (0, 0, 1, 1),
        (0, 1, 1, 1)
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 20, "min": 5, "max": 5},
        {"sum": 10, "min": 5, "max": 5}
    ]

    # ---------------------------------------------------------
    # Test 7: Negative values.
    # ---------------------------------------------------------
    matrix = [
        [-5, -2],
        [-9, -1]
    ]

    queries = [
        (0, 0, 1, 1),
        (0, 0, 0, 1),
        (1, 0, 1, 1)
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": -17, "min": -9, "max": -1},
        {"sum": -7, "min": -5, "max": -2},
        {"sum": -10, "min": -9, "max": -1}
    ]

    # ---------------------------------------------------------
    # Test 8: Single-cell queries inside a larger matrix.
    # ---------------------------------------------------------
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]

    queries = [
        (0, 0, 0, 0),
        (1, 1, 1, 1),
        (2, 2, 2, 2)
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 1, "min": 1, "max": 1},
        {"sum": 5, "min": 5, "max": 5},
        {"sum": 9, "min": 9, "max": 9}
    ]

    # ---------------------------------------------------------
    # Test 9: Multiple disconnected query rectangles.
    # The rectangles do not need to touch each other.
    # ---------------------------------------------------------
    matrix = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
        [13, 14, 15, 16]
    ]

    queries = [
        (0, 0, 0, 0),
        (3, 3, 3, 3),
        (0, 3, 1, 3),
        (2, 0, 3, 1)
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 1, "min": 1, "max": 1},
        {"sum": 16, "min": 16, "max": 16},
        {"sum": 12, "min": 4, "max": 8},
        {"sum": 46, "min": 9, "max": 14}
    ]

    # ---------------------------------------------------------
    # Test 10: Query order must be preserved.
    # ---------------------------------------------------------
    matrix = [
        [1, 2],
        [3, 4]
    ]

    queries = [
        (1, 1, 1, 1),
        (0, 0, 0, 0),
        (0, 0, 1, 1)
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 4, "min": 4, "max": 4},
        {"sum": 1, "min": 1, "max": 1},
        {"sum": 10, "min": 1, "max": 4}
    ]

    # ---------------------------------------------------------
    # Test 11: Invalid query on an empty matrix.
    # ---------------------------------------------------------
    try:
        rectangle_statistics([], [(0, 0, 0, 0)])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # ---------------------------------------------------------
    # Test 12: Invalid reversed rectangle.
    # ---------------------------------------------------------
    try:
        rectangle_statistics([[1, 2], [3, 4]], [(1, 1, 0, 0)])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # ---------------------------------------------------------
    # Test 13: Non-rectangular matrix.
    # ---------------------------------------------------------
    try:
        rectangle_statistics([[1, 2], [3]], [])
        assert False, "Expected ValueError"
    except ValueError:
        pass

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()