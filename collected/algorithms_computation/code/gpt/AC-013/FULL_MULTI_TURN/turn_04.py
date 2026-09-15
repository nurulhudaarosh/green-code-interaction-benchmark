# Rectangle Statistics Engine
#
# Problem:
# Given an integer matrix and a list of inclusive rectangle queries,
# return the sum, minimum, and maximum value for every queried rectangle.
#
# Original required output:
# {
#     "sum": ...,
#     "min": ...,
#     "max": ...
# }
#
# The algorithm must:
# - Build a 2D prefix-sum table for rectangle sums.
# - Use O(1) prefix-sum queries for sums.
# - Directly scan each requested rectangle for minimum and maximum.
# - Handle repeated minimum/maximum values deterministically.
# - Return values only for min/max; no position is selected on ties.
#
# Difficult valid cases handled here:
# 1. Smallest permitted input:
#       A 1x1 matrix with one 1x1 query.
# 2. Empty structures where allowed:
#       An empty matrix with no queries returns [].
#       A matrix with no queries returns [].
#
# An empty matrix cannot have a valid rectangle query, so supplying
# queries for an empty matrix raises ValueError.
#
# No unrelated output fields are added by default.
# The optional operation_summary feature from the previous version
# remains available and is unchanged when explicitly requested.


from typing import List, Tuple, Dict, Any


def rectangle_statistics(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]],
    include_operation_summary: bool = False
) -> List[Dict[str, Any]]:
    """
    Return statistics for inclusive rectangle queries.

    Each query is:
        (r1, c1, r2, c2)

    Required output:
        {
            "sum": ...,
            "min": ...,
            "max": ...
        }

    If include_operation_summary=True, also return:
        "operation_summary": deterministic operation count
    """

    # ---------------------------------------------------------
    # Empty matrix.
    # ---------------------------------------------------------
    if not matrix:
        if queries:
            raise ValueError(
                "Queries cannot be answered for an empty matrix."
            )
        return []

    rows = len(matrix)
    cols = len(matrix[0])

    # Empty rows are allowed only when there are no queries.
    if cols == 0:
        if queries:
            raise ValueError(
                "Queries cannot be answered for an empty matrix."
            )
        return []

    # The matrix must be rectangular.
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
    # Process each rectangle query.
    # ---------------------------------------------------------
    for query in queries:
        if len(query) != 4:
            raise ValueError(
                "Each query must contain four coordinates."
            )

        r1, c1, r2, c2 = query

        # Inclusive rectangle validation.
        if not (
            0 <= r1 <= r2 < rows
            and 0 <= c1 <= c2 < cols
        ):
            raise ValueError(f"Invalid rectangle query: {query}")

        # -----------------------------------------------------
        # Sum using the 2D prefix-sum table.
        # -----------------------------------------------------
        rectangle_sum = (
            prefix[r2 + 1][c2 + 1]
            - prefix[r1][c2 + 1]
            - prefix[r2 + 1][c1]
            + prefix[r1][c1]
        )

        # -----------------------------------------------------
        # Direct scan for minimum and maximum.
        #
        # Equal values do not require a tie decision because
        # only the value, not its coordinate, is returned.
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

        # Preserve the original required fields exactly.
        result = {
            "sum": rectangle_sum,
            "min": minimum,
            "max": maximum
        }

        # Optional feature remains disabled by default.
        if include_operation_summary:
            result["operation_summary"] = (
                1
                + cells_scanned
                + min_comparisons
                + max_comparisons
            )

        results.append(result)

    return results


# =============================================================
# TESTS
# =============================================================

if __name__ == "__main__":

    # ---------------------------------------------------------
    # Test 1: Smallest permitted input.
    # 1x1 matrix and one 1x1 rectangle.
    # ---------------------------------------------------------
    assert rectangle_statistics(
        [[5]],
        [(0, 0, 0, 0)]
    ) == [
        {
            "sum": 5,
            "min": 5,
            "max": 5
        }
    ]

    # ---------------------------------------------------------
    # Test 2: Empty matrix with no queries.
    # This is an allowed empty structure and returns no results.
    # ---------------------------------------------------------
    assert rectangle_statistics(
        [],
        []
    ) == []

    # ---------------------------------------------------------
    # Test 3: Matrix exists but there are no queries.
    # No unnecessary output is produced.
    # ---------------------------------------------------------
    assert rectangle_statistics(
        [[1, 2], [3, 4]],
        []
    ) == []

    # ---------------------------------------------------------
    # Test 4: Empty row structure with no queries.
    # ---------------------------------------------------------
    assert rectangle_statistics(
        [[]],
        []
    ) == []

    # ---------------------------------------------------------
    # Test 5: Empty matrix with a query is invalid because
    # there is no rectangle to query.
    # ---------------------------------------------------------
    try:
        rectangle_statistics(
            [],
            [(0, 0, 0, 0)]
        )
        assert False, "Expected ValueError for empty matrix query."
    except ValueError:
        pass

    # ---------------------------------------------------------
    # Test 6: Tied minimum and maximum.
    # Deterministic output is based on values, not positions.
    # ---------------------------------------------------------
    assert rectangle_statistics(
        [
            [2, 1],
            [1, 2]
        ],
        [(0, 0, 1, 1)]
    ) == [
        {
            "sum": 6,
            "min": 1,
            "max": 2
        }
    ]

    # ---------------------------------------------------------
    # Test 7: Multiple rectangles.
    # ---------------------------------------------------------
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

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 12, "min": 1, "max": 5},
        {"sum": 28, "min": 5, "max": 9},
        {"sum": 45, "min": 1, "max": 9}
    ]

    # ---------------------------------------------------------
    # Test 8: Smallest input with operation_summary enabled.
    # For a 1x1 rectangle:
    # 1 prefix operation + 1 cell scan
    # + 1 min comparison + 1 max comparison = 4.
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
    # Test 9: Disconnected/independent queries.
    # Each rectangle is processed independently; there is no
    # requirement that queried rectangles touch or connect.
    # ---------------------------------------------------------
    matrix = [
        [10, 20, 30, 40],
        [50, 60, 70, 80],
        [90, 100, 110, 120],
        [130, 140, 150, 160]
    ]

    queries = [
        (0, 0, 0, 0),  # single cell
        (3, 3, 3, 3),  # distant single cell
        (0, 2, 1, 3)   # separate rectangle
    ]

    assert rectangle_statistics(matrix, queries) == [
        {"sum": 10, "min": 10, "max": 10},
        {"sum": 160, "min": 160, "max": 160},
        {"sum": 300, "min": 30, "max": 80}
    ]

    print("All tests passed.")