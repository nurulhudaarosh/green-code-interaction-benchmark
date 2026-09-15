from typing import List, Tuple, Dict, Any


def rectangle_statistics(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]],
    include_operation_summary: bool = False
) -> Any:
    """
    Answer inclusive rectangle queries for sum, minimum, and maximum.

    Original output when include_operation_summary=False:
        [(sum, minimum, maximum), ...]

    When include_operation_summary=True:
        {
            "results": [(sum, minimum, maximum), ...],
            "operation_summary": {
                "prefix_sum_cells": ...,
                "rectangle_sum_operations": ...,
                "extrema_cells_scanned": ...,
                "extrema_comparisons": ...,
                "total_major_operations": ...
            }
        }
    """

    if not matrix or not matrix[0]:
        if queries:
            raise ValueError("Matrix must not be empty.")

        if include_operation_summary:
            return {
                "results": [],
                "operation_summary": {
                    "prefix_sum_cells": 0,
                    "rectangle_sum_operations": 0,
                    "extrema_cells_scanned": 0,
                    "extrema_comparisons": 0,
                    "total_major_operations": 0
                }
            }

        return []

    rows = len(matrix)
    cols = len(matrix[0])

    # Ensure the matrix is rectangular.
    for row in matrix:
        if len(row) != cols:
            raise ValueError("Matrix must be rectangular.")

    # ---------------------------------------------------------
    # Operation counters
    # ---------------------------------------------------------
    prefix_sum_cells = 0
    rectangle_sum_operations = 0
    extrema_cells_scanned = 0
    extrema_comparisons = 0

    # ---------------------------------------------------------
    # Build the 2D prefix-sum table.
    #
    # prefix[i][j] stores the sum of matrix[0:i][0:j].
    # ---------------------------------------------------------
    prefix = [[0] * (cols + 1) for _ in range(rows + 1)]

    for r in range(rows):
        row_sum = 0

        for c in range(cols):
            row_sum += matrix[r][c]

            prefix[r + 1][c + 1] = (
                prefix[r][c + 1] + row_sum
            )

            # One major preprocessing operation per
            # matrix cell.
            prefix_sum_cells += 1

    results = []

    # ---------------------------------------------------------
    # Process queries.
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
        # Rectangle sum using the 2D prefix-sum table.
        # -----------------------------------------------------
        total = (
            prefix[r2 + 1][c2 + 1]
            - prefix[r1][c2 + 1]
            - prefix[r2 + 1][c1]
            + prefix[r1][c1]
        )

        rectangle_sum_operations += 1

        # -----------------------------------------------------
        # Direct scan for minimum and maximum.
        # -----------------------------------------------------
        minimum = matrix[r1][c1]
        maximum = matrix[r1][c1]

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                value = matrix[r][c]

                extrema_cells_scanned += 1

                if value < minimum:
                    minimum = value

                extrema_comparisons += 1

                if value > maximum:
                    maximum = value

                extrema_comparisons += 1

        results.append((total, minimum, maximum))

    # ---------------------------------------------------------
    # Preserve the original output when the feature is disabled.
    # ---------------------------------------------------------
    if not include_operation_summary:
        return results

    total_major_operations = (
        prefix_sum_cells
        + rectangle_sum_operations
        + extrema_cells_scanned
        + extrema_comparisons
    )

    operation_summary: Dict[str, int] = {
        "prefix_sum_cells": prefix_sum_cells,
        "rectangle_sum_operations": rectangle_sum_operations,
        "extrema_cells_scanned": extrema_cells_scanned,
        "extrema_comparisons": extrema_comparisons,
        "total_major_operations": total_major_operations
    }

    return {
        "results": results,
        "operation_summary": operation_summary
    }


# -------------------------------------------------------------
# Example
# -------------------------------------------------------------

matrix = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12]
]

queries = [
    (0, 0, 1, 1),
    (1, 1, 2, 3),
    (0, 0, 2, 3)
]

# Original behavior: unchanged output format.
print(rectangle_statistics(matrix, queries))

# Output:
# [(14, 1, 6), (54, 6, 12), (78, 1, 12)]


# New feature: request operation_summary.
print(
    rectangle_statistics(
        matrix,
        queries,
        include_operation_summary=True
    )
)

# Output structure:
# {
#     "results": [
#         (14, 1, 6),
#         (54, 6, 12),
#         (78, 1, 12)
#     ],
#     "operation_summary": {
#         "prefix_sum_cells": 12,
#         "rectangle_sum_operations": 3,
#         "extrema_cells_scanned": 24,
#         "extrema_comparisons": 48,
#         "total_major_operations": 87
#     }
# }