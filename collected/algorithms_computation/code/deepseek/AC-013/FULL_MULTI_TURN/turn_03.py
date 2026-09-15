from typing import List, Tuple, Optional, Dict


class RectangleStatisticsEngine:
    """Preprocess an integer matrix for sum/min/max rectangle queries.

    Contract:
      * sum  -> O(1) via 2D prefix sums.
      * min/max -> O(area) direct scan.
      * Deterministic tie handling: among tied extremal cells, the reported
        representative is the one with the smallest (row, col), independent
        of scan order. `query` returns the extremal values themselves.

    Optional feature (disabled by default):
      * When enable_operation_summary=True, the engine tracks the number of
        major computational decisions/operations per call and exposes them
        via `query_with_summary` and `last_operation_summary`. All original
        fields and return shapes remain unchanged.
    """

    def __init__(self, matrix: List[List[int]],
                 enable_operation_summary: bool = False) -> None:
        if not matrix or not matrix[0]:
            raise ValueError("Matrix must be non-empty.")
        self.rows = len(matrix)
        self.cols = len(matrix[0])
        if any(len(row) != self.cols for row in matrix):
            raise ValueError("Matrix rows must all have the same length.")

        self.matrix = matrix
        self.enable_operation_summary = enable_operation_summary
        self.last_operation_summary: Optional[Dict[str, int]] = None

        # Build prefix sum and count one major decision per cell.
        build_decisions = 0
        self.prefix = [[0] * (self.cols + 1) for _ in range(self.rows + 1)]
        for i in range(self.rows):
            row_sum = 0
            pi = self.prefix[i]
            pi1 = self.prefix[i + 1]
            mi = matrix[i]
            for j in range(self.cols):
                row_sum += mi[j]
                pi1[j + 1] = pi[j + 1] + row_sum
                build_decisions += 1
        self._build_decisions = build_decisions

    # -------- validation --------
    def _validate(self, r1: int, c1: int, r2: int, c2: int) -> None:
        if not (0 <= r1 <= r2 < self.rows and 0 <= c1 <= c2 < self.cols):
            raise IndexError(
                f"Invalid rectangle ({r1},{c1})-({r2},{c2}) "
                f"for matrix {self.rows}x{self.cols}."
            )

    # -------- core aggregates (unchanged behavior) --------
    def rect_sum(self, r1: int, c1: int, r2: int, c2: int) -> int:
        self._validate(r1, c1, r2, c2)
        P = self.prefix
        # 4 constant inclusion-exclusion decisions.
        return P[r2 + 1][c2 + 1] - P[r1][c2 + 1] - P[r2 + 1][c1] + P[r1][c1]

    def rect_min_with_cell(self, r1: int, c1: int, r2: int, c2: int
                           ) -> Tuple[int, Tuple[int, int]]:
        self._validate(r1, c1, r2, c2)
        best: Optional[Tuple[int, int, int]] = None  # (value, row, col)
        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                cand = (row[j], i, j)
                if best is None or cand < best:
                    best = cand
        v, i, j = best  # type: ignore[misc]
        return v, (i, j)

    def rect_max_with_cell(self, r1: int, c1: int, r2: int, c2: int
                           ) -> Tuple[int, Tuple[int, int]]:
        self._validate(r1, c1, r2, c2)
        best: Optional[Tuple[int, int, int]] = None  # (-value, row, col)
        for i in range(r1, r2 + 1):
            row = self.matrix[i]
            for j in range(c1, c2 + 1):
                cand = (-row[j], i, j)
                if best is None or cand < best:
                    best = cand
        neg_v, i, j = best  # type: ignore[misc]
        return -neg_v, (i, j)

    def rect_min(self, r1: int, c1: int, r2: int, c2: int) -> int:
        return self.rect_min_with_cell(r1, c1, r2, c2)[0]

    def rect_max(self, r1: int, c1: int, r2: int, c2: int) -> int:
        return self.rect_max_with_cell(r1, c1, r2, c2)[0]

    # -------- public query (unchanged shape) --------
    def query(self, r1: int, c1: int, r2: int, c2: int) -> Tuple[int, int, int]:
        return (
            self.rect_sum(r1, c1, r2, c2),
            self.rect_min(r1, c1, r2, c2),
            self.rect_max(r1, c1, r2, c2),
        )

    def query_full(self, r1: int, c1: int, r2: int, c2: int):
        s = self.rect_sum(r1, c1, r2, c2)
        mn, mn_cell = self.rect_min_with_cell(r1, c1, r2, c2)
        mx, mx_cell = self.rect_max_with_cell(r1, c1, r2, c2)
        return s, (mn, mn_cell), (mx, mx_cell)

    # -------- optional operation-summary feature --------
    def _count_operations(self, r1: int, c1: int, r2: int, c2: int) -> Dict[str, int]:
        area = (r2 - r1 + 1) * (c2 - c1 + 1)
        summary = {
            "preprocessing_decisions": self._build_decisions,
            "sum_decisions": 4,               # 4-term inclusion-exclusion
            "min_decisions": area,            # one compare per scanned cell
            "max_decisions": area,            # one compare per scanned cell
            "query_decisions": 4 + 2 * area,  # per-query decisions
            "total_decisions": self._build_decisions + 4 + 2 * area,
        }
        return summary

    def query_with_summary(self, r1: int, c1: int, r2: int, c2: int):
        """Return (sum, min, max, operation_summary).

        operation_summary is populated only when the feature is enabled;
        when disabled, it is None, preserving the original behavior.
        """
        result = self.query(r1, c1, r2, c2)
        if self.enable_operation_summary:
            summary = self._count_operations(r1, c1, r2, c2)
            self.last_operation_summary = summary
            return result + (summary,)
        self.last_operation_summary = None
        return result + (None,)


def _demo() -> None:
    M = [[5, 1, 5],
         [1, 5, 1],
         [5, 1, 5]]

    # --- Feature disabled: original behavior fully preserved ---
    eng_off = RectangleStatisticsEngine(M)
    assert eng_off.query(0, 0, 2, 2) == (27, 1, 5)
    assert eng_off.query(0, 0, 0, 0) == (5, 5, 5)
    assert eng_off.query_full(0, 0, 2, 2) == (27, (1, (0, 1)), (5, (0, 0)))
    s, mn, mx, summary = eng_off.query_with_summary(0, 0, 2, 2)
    assert (s, mn, mx) == (27, 1, 5)
    assert summary is None
    assert eng_off.last_operation_summary is None

    # --- Feature enabled: summary is populated, core values unchanged ---
    eng_on = RectangleStatisticsEngine(M, enable_operation_summary=True)
    assert eng_on.query(0, 0, 2, 2) == (27, 1, 5)
    s, mn, mx, summary = eng_on.query_with_summary(0, 0, 2, 2)
    assert (s, mn, mx) == (27, 1, 5)
    # 3x3: preprocessing = 9, area = 9, query_decisions = 4 + 18 = 22
    assert summary == {
        "preprocessing_decisions": 9,
        "sum_decisions": 4,
        "min_decisions": 9,
        "max_decisions": 9,
        "query_decisions": 22,
        "total_decisions": 31,
    }
    assert eng_on.last_operation_summary == summary

    # Determinism: identical queries -> identical summaries.
    s2, mn2, mx2, summary2 = eng_on.query_with_summary(0, 0, 2, 2)
    assert (s2, mn2, mx2) == (s, mn, mx)
    assert summary2 == summary

    # Smaller rectangle: area = 2, query_decisions = 4 + 4 = 8, total = 17
    _, _, _, small = eng_on.query_with_summary(0, 0, 0, 1)
    assert small["min_decisions"] == 2
    assert small["max_decisions"] == 2
    assert small["query_decisions"] == 8
    assert small["total_decisions"] == 17

    print("All checks passed (operation_summary feature verified; "
          "original behavior preserved when disabled).")


if __name__ == "__main__":
    _demo()