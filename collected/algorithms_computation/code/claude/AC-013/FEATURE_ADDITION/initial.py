"""
Matrix Range Query Processor
=============================

Preprocesses an integer matrix and answers inclusive rectangle queries for:
  - sum  : total of all values in the rectangle
  - min  : minimum value in the rectangle
  - max  : maximum value in the rectangle

Design (intentionally mixed workload):
  - SUM queries use a 2D prefix-sum table built once in O(R*C), giving O(1)
    per query via inclusion-exclusion.
  - MIN / MAX queries have no auxiliary structure; each query directly scans
    the requested rectangle in O(area) time.

Deterministic, standard-library only. No network, no randomness, no I/O
beyond the demonstration's own print statements.
"""

from typing import List, Tuple, Union

Number = Union[int, float]


class MatrixRangeQuery:
    """Preprocesses a matrix and answers inclusive rectangle sum/min/max queries."""

    def __init__(self, matrix: List[List[Number]]):
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")

        row_len = len(matrix[0])
        for row in matrix:
            if len(row) != row_len:
                raise ValueError("All rows must have the same length.")

        self.matrix = matrix
        self.rows = len(matrix)
        self.cols = row_len
        self.prefix_sum = self._build_prefix_sum(matrix)

    # ---------- Preprocessing ----------

    def _build_prefix_sum(self, matrix: List[List[Number]]) -> List[List[Number]]:
        """
        Build a (rows+1) x (cols+1) prefix-sum table P where
        P[i][j] = sum of all matrix[a][b] with a < i and b < j.
        O(rows * cols) time and space.
        """
        rows, cols = self.rows, self.cols
        prefix = [[0] * (cols + 1) for _ in range(rows + 1)]

        for i in range(1, rows + 1):
            row_running_sum = 0
            for j in range(1, cols + 1):
                row_running_sum += matrix[i - 1][j - 1]
                prefix[i][j] = prefix[i - 1][j] + row_running_sum

        return prefix

    # ---------- Validation ----------

    def _validate_rectangle(self, row1: int, col1: int, row2: int, col2: int) -> None:
        if not (0 <= row1 <= row2 < self.rows):
            raise ValueError(
                f"Invalid row range: row1={row1}, row2={row2}, rows={self.rows}"
            )
        if not (0 <= col1 <= col2 < self.cols):
            raise ValueError(
                f"Invalid col range: col1={col1}, col2={col2}, cols={self.cols}"
            )

    # ---------- Query: sum (O(1), uses prefix-sum table) ----------

    def query_sum(self, row1: int, col1: int, row2: int, col2: int) -> Number:
        """Inclusive rectangle sum via inclusion-exclusion on the prefix-sum table."""
        self._validate_rectangle(row1, col1, row2, col2)
        p = self.prefix_sum
        total = (
            p[row2 + 1][col2 + 1]
            - p[row1][col2 + 1]
            - p[row2 + 1][col1]
            + p[row1][col1]
        )
        return total

    # ---------- Query: min / max (O(area), direct scan) ----------

    def query_min(self, row1: int, col1: int, row2: int, col2: int) -> Number:
        """Inclusive rectangle minimum via direct scan (no precomputed structure)."""
        self._validate_rectangle(row1, col1, row2, col2)
        m = self.matrix
        best = m[row1][col1]
        for i in range(row1, row2 + 1):
            row = m[i]
            for j in range(col1, col2 + 1):
                v = row[j]
                if v < best:
                    best = v
        return best

    def query_max(self, row1: int, col1: int, row2: int, col2: int) -> Number:
        """Inclusive rectangle maximum via direct scan (no precomputed structure)."""
        self._validate_rectangle(row1, col1, row2, col2)
        m = self.matrix
        best = m[row1][col1]
        for i in range(row1, row2 + 1):
            row = m[i]
            for j in range(col1, col2 + 1):
                v = row[j]
                if v > best:
                    best = v
        return best

    # ---------- Unified dispatch ----------

    def query(self, op: str, row1: int, col1: int, row2: int, col2: int) -> Number:
        """
        Dispatch a query by operation name: 'sum', 'min', or 'max'.
        Raises ValueError for unsupported operations or out-of-bounds rectangles.
        """
        op = op.lower()
        if op == "sum":
            return self.query_sum(row1, col1, row2, col2)
        elif op == "min":
            return self.query_min(row1, col1, row2, col2)
        elif op == "max":
            return self.query_max(row1, col1, row2, col2)
        else:
            raise ValueError(f"Unsupported operation: {op!r} (expected 'sum', 'min', or 'max')")


def run_queries(
    matrix: List[List[Number]],
    queries: List[Tuple[str, int, int, int, int]],
) -> List[Number]:
    """
    Convenience batch runner.
    queries: list of (op, row1, col1, row2, col2) tuples.
    Returns results in the same order as the input queries.
    """
    solver = MatrixRangeQuery(matrix)
    return [solver.query(op, r1, c1, r2, c2) for (op, r1, c1, r2, c2) in queries]


# ---------------------------------------------------------------------------
# Brute-force reference (used only for self-check / correctness verification)
# ---------------------------------------------------------------------------

def _brute_force(matrix, op, row1, col1, row2, col2):
    values = [matrix[i][j] for i in range(row1, row2 + 1) for j in range(col1, col2 + 1)]
    if op == "sum":
        return sum(values)
    elif op == "min":
        return min(values)
    elif op == "max":
        return max(values)
    raise ValueError(op)


def _self_check():
    """Deterministic correctness check against brute force over a fixed matrix."""
    matrix = [
        [3, -1, 4, 1, 5],
        [9, 2, 6, -5, 3],
        [5, 8, 9, 7, -9],
        [3, 2, 3, 8, 4],
    ]
    solver = MatrixRangeQuery(matrix)

    rows, cols = len(matrix), len(matrix[0])
    all_ok = True
    for row1 in range(rows):
        for row2 in range(row1, rows):
            for col1 in range(cols):
                for col2 in range(col1, cols):
                    for op in ("sum", "min", "max"):
                        expected = _brute_force(matrix, op, row1, col1, row2, col2)
                        actual = solver.query(op, row1, col1, row2, col2)
                        if expected != actual:
                            all_ok = False
                            print(
                                f"MISMATCH op={op} rect=({row1},{col1},{row2},{col2}) "
                                f"expected={expected} actual={actual}"
                            )
    print("Self-check:", "ALL PASSED" if all_ok else "FAILURES FOUND")


def _demo():
    matrix = [
        [3, -1, 4, 1, 5],
        [9, 2, 6, -5, 3],
        [5, 8, 9, 7, -9],
        [3, 2, 3, 8, 4],
    ]

    print("Matrix:")
    for row in matrix:
        print(" ", row)
    print()

    queries = [
        ("sum", 0, 0, 3, 4),   # whole matrix
        ("sum", 1, 1, 2, 3),
        ("min", 1, 1, 2, 3),
        ("max", 1, 1, 2, 3),
        ("min", 0, 0, 0, 0),   # single cell
        ("max", 2, 2, 2, 2),   # single cell
        ("sum", 0, 4, 3, 4),   # single column
        ("min", 2, 0, 3, 4),   # last two rows
    ]

    results = run_queries(matrix, queries)
    for (op, r1, c1, r2, c2), result in zip(queries, results):
        print(f"query({op!r}, rows[{r1}:{r2}], cols[{c1}:{c2}]) -> {result}")

    print()
    _self_check()


if __name__ == "__main__":
    _demo()