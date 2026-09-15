from typing import List, Tuple


def preprocess_prefix_sum(matrix: List[List[int]]) -> List[List[int]]:
    """Build a 2D prefix-sum table."""
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


def get_rectangle_sum(
    prefix: List[List[int]],
    r1: int,
    c1: int,
    r2: int,
    c2: int
) -> int:
    """Return the sum of an inclusive rectangle."""
    return (
        prefix[r2 + 1][c2 + 1]
        - prefix[r1][c2 + 1]
        - prefix[r2 + 1][c1]
        + prefix[r1][c1]
    )


def rectangle_statistics(
    matrix: List[List[int]],
    queries: List[Tuple[int, int, int, int]]
) -> List[Tuple[int, int, int]]:
    """
    Return (sum, minimum, maximum) for each inclusive
    rectangle query, preserving query order.
    """
    if not matrix or not matrix[0]:
        if queries:
            raise ValueError("Matrix must not be empty.")
        return []

    rows = len(matrix)
    cols = len(matrix[0])

    # The matrix must be rectangular.
    if any(len(row) != cols for row in matrix):
        raise ValueError("Matrix must be rectangular.")

    prefix = preprocess_prefix_sum(matrix)
    results = []

    for r1, c1, r2, c2 in queries:
        # Validate inclusive rectangle coordinates.
        if not (
            0 <= r1 <= r2 < rows
            and 0 <= c1 <= c2 < cols
        ):
            raise ValueError(
                f"Invalid rectangle query: {(r1, c1, r2, c2)}"
            )

        # Sum: O(1) using the 2D prefix-sum table.
        total = get_rectangle_sum(
            prefix, r1, c1, r2, c2
        )

        # Extrema: direct inclusive rectangle scan.
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


# Small regression test demonstrating the corrected behavior.
if __name__ == "__main__":
    matrix = [
        [1, 2],
        [3, 100]
    ]

    queries = [
        (0, 0, 1, 1)
    ]

    expected = [
        (106, 1, 100)
    ]

    actual = rectangle_statistics(matrix, queries)

    assert actual == expected, (
        f"Expected {expected}, got {actual}"
    )

    print(actual)