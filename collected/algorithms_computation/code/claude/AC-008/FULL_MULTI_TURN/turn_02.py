class FenwickTree:
    """Binary Indexed Tree supporting point updates and prefix-sum queries in O(log n)."""

    __slots__ = ("n", "tree")

    def __init__(self, n: int):
        self.n = n
        self.tree = [0] * (n + 1)  # 1-indexed internally

    def add(self, index: int, delta: int) -> None:
        """Add `delta` to the element at 0-based `index`."""
        i = index + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)

    def prefix_sum(self, index: int) -> int:
        """Sum of elements in [0, index] (0-based, inclusive). Returns 0 for index == -1."""
        if index == -1:
            return 0
        if index < -1:
            raise ValueError(f"invalid prefix index: {index}")
        i = index + 1
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & (-i)
        return total

    def range_sum(self, left: int, right: int) -> int:
        """Sum of elements in [left, right] (0-based, inclusive). left == right is the
        deterministic single-element case; left > right is rejected, not coerced to 0."""
        if left > right:
            raise ValueError(f"invalid range: left={left} > right={right}")
        return self.prefix_sum(right) - self.prefix_sum(left - 1)


class ArrayWithRangeSum:
    """
    Maintains an integer array under point replacement and inclusive
    range-sum queries, backed by a Fenwick tree, with deterministic
    handling of tie/boundary cases (equal indices, zero-delta writes,
    degenerate ranges).
    """

    def __init__(self, initial: list):
        self.n = len(initial)
        self.values = list(initial)          # current array values (always kept in sync)
        self.tree = FenwickTree(self.n)
        for idx, val in enumerate(initial):
            if val != 0:
                self.tree.add(idx, val)

    def _check_index(self, index: int) -> None:
        if not isinstance(index, int) or not (0 <= index < self.n):
            raise IndexError(f"index {index} out of bounds for array of size {self.n}")

    def update(self, index: int, new_value: int) -> None:
        """Point replacement: set array[index] = new_value.
        Deterministic even when new_value equals the current value: the shadow
        array is always reassigned, and the Fenwick tree is only touched when
        the delta is non-zero (a pure optimization, not a behavioral branch)."""
        self._check_index(index)
        delta = new_value - self.values[index]
        self.values[index] = new_value      # always reassign: no hidden branch on equality
        if delta != 0:
            self.tree.add(index, delta)

    def query(self, left: int, right: int) -> int:
        """Inclusive range-sum query over array[left..right].
        left == right (a tie) is valid and returns the single element.
        left > right is a hard error, never silently coerced to 0."""
        self._check_index(left)
        self._check_index(right)
        if left > right:
            raise ValueError(f"invalid range: left={left} > right={right}")
        return self.tree.range_sum(left, right)


def process_operations(initial: list, operations: list) -> list:
    """
    initial: starting array of integers.
    operations: list of tuples, each either
        ("update", index, new_value)
        ("query", left, right)
    Returns: list of results for each "query" operation, in order.
    """
    structure = ArrayWithRangeSum(initial)
    results = []
    for op in operations:
        kind = op[0]
        if kind == "update":
            _, index, new_value = op
            structure.update(index, new_value)
        elif kind == "query":
            _, left, right = op
            results.append(structure.query(left, right))
        else:
            raise ValueError(f"unknown operation type: {kind}")
    return results


if __name__ == "__main__":
    # Regression test reproducing the original defect
    initial_array = [4, 4]
    ops_regression = [
        ("update", 0, 4),   # replacement to the same value: must not desync shadow array
        ("query", 0, 0),    # deterministic tie case: single element -> 4
    ]
    result = process_operations(initial_array, ops_regression)
    assert result == [4], f"Regression failed: {result}"

    # Malformed range must now raise, not silently return 0
    try:
        process_operations(initial_array, [("query", 0, -1)])
        raised = False
    except ValueError:
        raised = True
    assert raised, "Malformed range (left > right) must raise, not return 0"

    # Original functional test
    base_array = [1, 3, 5, 7, 9, 11]
    ops = [
        ("query", 1, 3),
        ("update", 1, 10),
        ("query", 1, 3),
        ("update", 4, 0),
        ("query", 0, 5),
        ("query", 2, 2),
    ]
    output = process_operations(base_array, ops)
    assert output == [15, 22, 34, 5], f"Self-test failed: {output}"

    print("All tests passed.")