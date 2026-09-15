from typing import List, Tuple


def rectangle_statistics(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]]
) -> List[Tuple[int, int, int]]:
    """
    Answer inclusive rectangle queries for sum, minimum, and maximum.

    Each query is:
        (r1, c1, r2, c2)

    where:
        r1 <= r2
        c1 <= c2

    Returns:
        [(sum, minimum, maximum), ...]
    """

    if not matrix or not matrix[0]:
        if queries:
            raise ValueError("Matrix must not be empty.")
        return []

    rows = len(matrix)
    cols = len(matrix[0])

    # Ensure the matrix is rectangular.
    for row in matrix:
        if len(row) != cols:
            raise ValueError("Matrix must be rectangular.")

    # ---------------------------------------------------------
    # Step 1: Build a 2D prefix-sum table.
    #
    # prefix[i][j] stores the sum of matrix[0:i][0:j].
    # The extra first row and first column contain zeros.
    # ---------------------------------------------------------
    prefix = [[0] * (cols + 1) for _ in range(rows + 1)]

    for r in range(rows):
        row_sum = 0
        for c in range(cols):
            row_sum += matrix[r][c]
            prefix[r + 1][c + 1] = (
                prefix[r][c + 1]
                + row_sum
            )

    results = []

    # ---------------------------------------------------------
    # Step 2: Process each query.
    # ---------------------------------------------------------
    for r1, c1, r2, c2 in queries:

        # Validate coordinates.
        if not (
            0 <= r1 <= r2 < rows
            and 0 <= c1 <= c2 < cols
        ):
            raise ValueError(
                f"Invalid rectangle query: {(r1, c1, r2, c2)}"
            )

        # -----------------------------------------------------
        # Sum in O(1) using the 2D prefix-sum formula.
        # -----------------------------------------------------
        total = (
            prefix[r2 + 1][c2 + 1]
            - prefix[r1][c2 + 1]
            - prefix[r2 + 1][c1]
            + prefix[r1][c1]
        )

        # -----------------------------------------------------
        # Minimum and maximum by direct rectangle scanning.
        # -----------------------------------------------------
        minimum = matrix[r1][c1]
        maximum = matrix[r1][c1]

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                value = matrix[r][c]

                if value < minimum:
                    minimum = value

                if value > maximum:
                    maximum = value

        results.append((total, minimum, maximum))

    return results


# -------------------------------------------------------------
# Example
# -------------------------------------------------------------

matrix = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12]
]

queries = [
    (0, 0, 1, 1),  # [[1, 2], [5, 6]]
    (1, 1, 2, 3),  # [[6, 7, 8], [10, 11, 12]]
    (0, 0, 2, 3)   # Entire matrix
]

print(rectangle_statistics(matrix, queries))

# Output:
# [(14, 1, 6), (54, 6, 12), (78, 1, 12)]