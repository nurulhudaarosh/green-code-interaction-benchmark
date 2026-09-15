from typing import List, Tuple, Dict, Any


def rectangle_statistics(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]]
) -> List[Dict[str, int]]:
    """
    Answer inclusive rectangle queries for sum, minimum, and maximum.

    Each query is:
        (r1, c1, r2, c2)

    where:
        0 <= r1 <= r2 < number of rows
        0 <= c1 <= c2 < number of columns

    Returns:
        A list of dictionaries, one per query:
        {
            "sum": rectangle_sum,
            "min": rectangle_minimum,
            "max": rectangle_maximum
        }

    Algorithm:
        - Build a 2D prefix-sum table for O(1) rectangle sums.
        - Scan each queried rectangle directly for minimum and maximum.
    """

    # Validate the matrix.
    if not matrix:
        if queries:
            raise ValueError("Queries cannot be answered for an empty matrix.")
        return []

    rows = len(matrix)
    cols = len(matrix[0])

    if cols == 0:
        if queries:
            raise ValueError("Queries cannot be answered for an empty matrix.")
        return []

    if any(len(row) != cols for row in matrix):
        raise ValueError("Matrix must be rectangular.")

    # ------------------------------------------------------------
    # Step 1: Build a 2D prefix-sum table.
    #
    # prefix[i][j] contains the sum of matrix[0:i][0:j],
    # using half-open indexing.
    # ------------------------------------------------------------
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

    # ------------------------------------------------------------
    # Step 2: Process each query.
    # ------------------------------------------------------------
    for query in queries:
        if len(query) != 4:
            raise ValueError("Each query must contain four coordinates.")

        r1, c1, r2, c2 = query

        # Validate coordinates.
        if not (
            0 <= r1 <= r2 < rows
            and 0 <= c1 <= c2 < cols
        ):
            raise ValueError(f"Invalid rectangle query: {query}")

        # --------------------------------------------------------
        # Sum using the 2D prefix-sum formula.
        #
        # Inclusive rectangle [r1:r2] x [c1:c2]
        # becomes half-open [r1:r2+1] x [c1:c2+1].
        # --------------------------------------------------------
        rectangle_sum = (
            prefix[r2 + 1][c2 + 1]
            - prefix[r1][c2 + 1]
            - prefix[r2 + 1][c1]
            + prefix[r1][c1]
        )

        # --------------------------------------------------------
        # Minimum and maximum by direct rectangle scanning.
        # --------------------------------------------------------
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


# ------------------------------------------------------------
# Example
# ------------------------------------------------------------
if __name__ == "__main__":
    matrix = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]

    queries = [
        (0, 0, 1, 1),  # [[1,2], [4,5]]
        (1, 1, 2, 2),  # [[5,6], [8,9]]
        (0, 0, 2, 2)   # Entire matrix
    ]

    print(rectangle_statistics(matrix, queries))