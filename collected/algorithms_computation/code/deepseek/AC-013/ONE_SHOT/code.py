def preprocess(matrix):
    """
    Build a 2D prefix sum table.
    prefix[i][j] = sum of matrix[0..i-1][0..j-1]
    """
    R = len(matrix)
    C = len(matrix[0]) if R > 0 else 0
    prefix = [[0] * (C + 1) for _ in range(R + 1)]
    for i in range(1, R + 1):
        for j in range(1, C + 1):
            prefix[i][j] = (
                matrix[i - 1][j - 1]
                + prefix[i - 1][j]
                + prefix[i][j - 1]
                - prefix[i - 1][j - 1]
            )
    return prefix


def rect_sum(prefix, r1, c1, r2, c2):
    """Inclusive rectangle sum using 2D prefix sums — O(1)."""
    return (
        prefix[r2 + 1][c2 + 1]
        - prefix[r1][c2 + 1]
        - prefix[r2 + 1][c1]
        + prefix[r1][c1]
    )


def rect_min_max(matrix, r1, c1, r2, c2):
    """Inclusive rectangle min and max by direct scan — O(area)."""
    mn = float("inf")
    mx = float("-inf")
    for i in range(r1, r2 + 1):
        row = matrix[i]
        for j in range(c1, c2 + 1):
            v = row[j]
            if v < mn:
                mn = v
            if v > mx:
                mx = v
    return mn, mx


def solve(matrix, queries):
    """
    matrix: list of lists of ints
    queries: list of (r1, c1, r2, c2)
    Returns: list of (sum, min, max)
    """
    if not matrix or not matrix[0]:
        return []

    prefix = preprocess(matrix)
    results = []
    for (r1, c1, r2, c2) in queries:
        s = rect_sum(prefix, r1, c1, r2, c2)
        mn, mx = rect_min_max(matrix, r1, c1, r2, c2)
        results.append((s, mn, mx))
    return results


# ---------------- Demonstration ----------------
if __name__ == "__main__":
    matrix = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9, 10, 11, 12],
        [13,14, 15, 16],
    ]

    queries = [
        (0, 0, 1, 1),   # top-left 2x2
        (1, 1, 2, 2),   # middle 2x2
        (0, 0, 3, 3),   # whole matrix
        (2, 0, 3, 1),   # bottom-left 2x2
    ]

    for q in queries:
        s, mn, mx = solve(matrix, [q])[0]
        print(f"Query {q}: sum={s}, min={mn}, max={mx}")