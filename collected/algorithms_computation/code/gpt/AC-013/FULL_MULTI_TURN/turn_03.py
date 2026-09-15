# Rectangle Statistics Engine
#
# Problem:
# Given an integer matrix and a list of inclusive rectangle queries,
# return the sum, minimum, and maximum value for every queried rectangle.
#
# Original required output for each query:
# {
#     "sum": ...,
#     "min": ...,
#     "max": ...
# }
#
# New feature:
# Each query result now also contains:
#     "operation_summary": ...
#
# For this task, operation_summary is a deterministic count of the
# major computational operations performed for that query:
#   - 1 operation for the O(1) prefix-sum calculation.
#   - 1 operation for each matrix cell inspected during the direct
#     min/max scan.
#   - 1 operation for each min comparison.
#   - 1 operation for each max comparison.
#
# Therefore, for a rectangle with H rows and W columns:
#     operation_summary = 1 + H*W + H*W + H*W
#                       = 1 + 3*H*W
#
# The original algorithm and outputs remain unchanged:
# - Build a 2D prefix-sum table for sums.
# - Directly scan each rectangle for minimum and maximum.
# - Rectangle coordinates are inclusive.
# - Repeated minimum/maximum values are handled deterministically.
# - No position is returned for tied extrema.
#
# If operation_summary is disabled/not requested, the original output
# remains exactly:
#     {"sum": ..., "min": ..., "max": ...}


from typing import List, Tuple, Dict, Any


def rectangle_statistics(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]],
    include_operation_summary: bool = False
) -> List[Dict[str, Any]]:
    """
    Rectangle Statistics Engine.

    For each inclusive query (r1, c1, r2, c2), returns:
        {
            "sum": rectangle sum,
            "min": rectangle minimum,
            "max": rectangle maximum
        }

    If include_operation_summary=True, an additional field is returned:
        "operation_summary": number of major computational
        decisions/operations for that query.

    Algorithm:
        1. Build a 2D prefix-sum table.
        2. Use it for O(1) rectangle sums.
        3. Directly scan each rectangle for minimum and maximum.
    """

    # Empty matrix.
    if not matrix:
        if queries:
            raise ValueError(
                "Queries cannot be answered for an empty matrix."
            )
        return []

    rows = len(matrix)
    cols = len(matrix[0])

    if cols == 0:
        if queries:
            raise ValueError(
                "Queries cannot be answered for an empty matrix."
            )
        return []

    # Matrix must be rectangular.
    if any(len(row) != cols for row in matrix):
        raise ValueError("Matrix must be rectangular.")

    # ---------------------------------------------------------
    # Build 2D prefix-sum table.
    # ---------------------------------------------------------
    prefix = [[0] * (cols + 1) for _ in range(rows + 1)]

    for r in range(rows):
        for c in range(cols):
            prefix[r + 1][c + 1] = (
                matrix[r][c]
                + prefix[r][c + 1]
                + prefix[r + 1][c]
                - prefix[r][c]
            )

    results = []

    # ---------------------------------------------------------
    # Process each query.
    # ---------------------------------------------------------
    for query in queries:
        if len(query) != 4:
            raise ValueError(
                "Each query must contain four coordinates."
            )

        r1, c1, r2, c2 = query

        if not (
            0 <= r1 <= r2 < rows
            and 0 <= c1 <= c2 < cols
        ):
            raise ValueError(f"Invalid rectangle query: {query}")

        # -----------------------------------------------------
        # Sum: one major O(1) prefix-sum operation.
        # -----------------------------------------------------
        rectangle_sum = (
            prefix[r2 + 1][c2 + 1]
            - prefix[r1][c2 + 1]
            - prefix[r2 + 1][c1]
            + prefix[r1][c1]
        )

        # -----------------------------------------------------
        # Direct scan for minimum and maximum.
        # -----------------------------------------------------
        minimum = matrix[r1][c1]
        maximum = matrix[r1][c1]

        cells_scanned = 0
        min_comparisons = 0
        max_comparisons = 0

        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                value = matrix[r][c]

                cells_scanned += 1

                min_comparisons += 1
                if value < minimum:
                    minimum = value

                max_comparisons += 1
                if value > maximum:
                    maximum = value

        # -----------------------------------------------------
        # Preserve all original fields.
        # -----------------------------------------------------
        result = {
            "sum": rectangle_sum,
            "min": minimum,
            "max": maximum
        }

        # -----------------------------------------------------
        # Add the new optional field only when requested.
        # -----------------------------------------------------
        if include_operation_summary:
            operation_summary = (
                1
                + cells_scanned
                + min_comparisons
                + max_comparisons
            )

            result["operation_summary"] = operation_summary

        results.append(result)

    return results


# =============================================================
# Tests
# =============================================================

if __name__ == "__main__":

    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]

    queries = [
        (0, 0, 1, 1),
        (1, 1, 2, 2),
        (0, 0, 2, 2)
    ]

    # ---------------------------------------------------------
    # Test 1: Original behavior remains unchanged when the
    # optional feature is disabled.
    # ---------------------------------------------------------
    expected_original = [
        {"sum": 12, "min": 1, "max": 5},
        {"sum": 28, "min": 5, "max": 9},
        {"sum": 45, "min": 1, "max": 9}
    ]

    assert rectangle_statistics(
        matrix,
        queries
    ) == expected_original

    # ---------------------------------------------------------
    # Test 2: operation_summary enabled.
    #
    # Query 1 covers 2x2 = 4 cells:
    # 1 prefix operation + 4 scans + 4 min comparisons
    # + 4 max comparisons = 13.
    #
    # Query 2: also 13.
    #
    # Query 3 covers 3x3 = 9 cells:
    # 1 + 9 + 9 + 9 = 28.
    # ---------------------------------------------------------
    expected_with_summary = [
        {
            "sum": 12,
            "min": 1,
            "max": 5,
            "operation_summary": 13
        },
        {
            "sum": 28,
            "min": 5,
            "max": 9,
            "operation_summary": 13
        },
        {
            "sum": 45,
            "min": 1,
            "max": 9,
            "operation_summary": 28
        }
    ]

    assert rectangle_statistics(
        matrix,
        queries,
        include_operation_summary=True
    ) == expected_with_summary

    # ---------------------------------------------------------
    # Test 3: Smallest valid matrix.
    # ---------------------------------------------------------
    assert rectangle_statistics(
        [[7]],
        [(0, 0, 0, 0)],
        include_operation_summary=True
    ) == [
        {
            "sum": 7,
            "min": 7,
            "max": 7,
            "operation_summary": 4
        }
    ]

    # ---------------------------------------------------------
    # Test 4: Tied minimum and maximum values.
    # Ties are deterministic because only the values are returned.
    # ---------------------------------------------------------
    assert rectangle_statistics(
        [
            [2, 1],
            [1, 2]
        ],
        [(0, 0, 1, 1)],
        include_operation_summary=True
    ) == [
        {
            "sum": 6,
            "min": 1,
            "max": 2,
            "operation_summary": 13
        }
    ]

    print("All tests passed.")