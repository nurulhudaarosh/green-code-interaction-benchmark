from typing import List, Tuple


def preprocess_matrix(matrix: List[List[int]]) -> List[List[int]]:
    """
    Build a 2D prefix-sum table.

    prefix[i][j] stores the sum of the submatrix from
    (0, 0) to (i-1, j-1), inclusive.
    """
    rows = len(matrix)
    cols = len(matrix[0])

    prefix = [[0] * (cols + 1) for _ in range(rows + 1)]

    for r in range(rows):
        row_sum = 0
        for c in range(cols):
            row_sum += matrix[r][c]
            prefix[r + 1][c + 1] = (
                prefix[r][c + 1] + row_sum
            )

    return prefix


def rectangle_sum(
    prefix: List[List[int]],
    r1: int,
    c1: int,
    r2: int,
    c2: int
) -> int:
    """
    Return the sum of the inclusive rectangle
    (r1, c1) to (r2, c2).
    """
    return (
        prefix[r2 + 1][c2 + 1]
        - prefix[r1][c2 + 1]
        - prefix[r2 + 1][c1]
        + prefix[r1][c1]
    )


def rectangle_queries(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]]
) -> List[Tuple[int, int, int]]:
    """
    Answer inclusive rectangle queries.

    Each query is:
        (r1, c1, r2, c2)

    Each result is:
        (sum, minimum, maximum)
    """
    if not matrix or not matrix[0]:
        if queries:
            raise ValueError("Matrix must not be empty.")
        return []

    rows = len(matrix)
    cols = len(matrix[0])

    # Ensure the matrix is rectangular.
    if any(len(row) != cols for row in matrix):
        raise ValueError("Matrix must be rectangular.")

    prefix = preprocess_matrix(matrix)

    results = []

    for r1, c1, r2, c2 in queries:
        # Validate query boundaries.
        if not (
            0 <= r1 <= r2 < rows
            and 0 <= c1 <= c2 < cols
        ):
            raise ValueError(
                f"Invalid rectangle query: {(r1, c1, r2, c2)}"
            )

        # Sum is answered in O(1).
        total = rectangle_sum(prefix, r1, c1, r2, c2)

        # Minimum and maximum are found by direct scanning.
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


# Example
if __name__ == "__main__":
    matrix = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12]
    ]

    queries = [
        (0, 0, 1, 1),  # [[1,2], [5,6]]
        (1, 1, 2, 3),  # [[6,7,8], [10,11,12]]
        (0, 0, 2, 3)   # Entire matrix
    ]

    print(rectangle_queries(matrix, queries))