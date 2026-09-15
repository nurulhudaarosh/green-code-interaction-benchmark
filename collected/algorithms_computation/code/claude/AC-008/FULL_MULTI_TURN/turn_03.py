class FenwickTree:
    """Binary Indexed Tree supporting point updates and prefix-sum queries in O(log n)."""

    __slots__ = ("n", "tree", "_count_ops", "update_node_touches", "query_node_touches")

    def __init__(self, n: int, count_ops: bool = False):
        self.n = n
        self.tree = [0] * (n + 1)  # 1-indexed internally
        self._count_ops = count_ops
        self.update_node_touches = 0
        self.query_node_touches = 0

    def add(self, index: int, delta: int) -> None:
        """Add `delta` to the element at 0-based `index`."""
        i = index + 1
        while i <= self.n:
            self.tree[i] += delta
            if self._count_ops:
                self.update_node_touches += 1
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
            if self._count_ops:
                self.query_node_touches += 1
            i -= i & (-i)
        return total

    def range_sum(self, left: int, right: int) -> int:
        """Sum of elements in [left, right] (0-based, inclusive)."""
        if left > right:
            raise ValueError(f"invalid range: left={left} > right={right}")
        return self.prefix_sum(right) - self.prefix_sum(left - 1)


class ArrayWithRangeSum:
    """
    Maintains an integer array under point replacement and inclusive
    range-sum queries, backed by a Fenwick tree, with deterministic
    handling of tie/boundary cases and optional operation counting.
    """

    def __init__(self, initial: list, track_summary: bool = False):
        self.n = len(initial)
        self.values = list(initial)
        self.track_summary = track_summary
        self.tree = FenwickTree(self.n, count_ops=track_summary)
        self.updates_processed = 0
        self.queries_processed = 0
        for idx, val in enumerate(initial):
            if val != 0:
                self.tree.add(idx, val)
        # Initial construction touches don't count as "operations" in the
        # summary — only touches made while servicing the given op sequence do.
        if track_summary:
            self.tree.update_node_touches = 0
            self.tree.query_node_touches = 0

    def _check_index(self, index: int) -> None:
        if not isinstance(index, int) or not (0 <= index < self.n):
            raise IndexError(f"index {index} out of bounds for array of size {self.n}")

    def update(self, index: int, new_value: int) -> None:
        self._check_index(index)
        delta = new_value - self.values[index]
        self.values[index] = new_value
        if delta != 0:
            self.tree.add(index, delta)
        if self.track_summary:
            self.updates_processed += 1

    def query(self, left: int, right: int) -> int:
        self._check_index(left)
        self._check_index(right)
        if left > right:
            raise ValueError(f"invalid range: left={left} > right={right}")
        result = self.tree.range_sum(left, right)
        if self.track_summary:
            self.queries_processed += 1
        return result

    def summary(self) -> dict:
        """Deterministic count of major computational decisions/operations made."""
        return {
            "updates_processed": self.updates_processed,
            "queries_processed": self.queries_processed,
            "fenwick_update_node_touches": self.tree.update_node_touches,
            "fenwick_query_node_touches": self.tree.query_node_touches,
            "total_fenwick_node_touches": (
                self.tree.update_node_touches + self.tree.query_node_touches
            ),
        }


def process_operations(initial: list, operations: list, include_summary: bool = False):
    """
    initial: starting array of integers.
    operations: list of tuples, each either
        ("update", index, new_value)
        ("query", left, right)
    include_summary: if False (default), returns a list of query results
        exactly as before — no change to the original contract.
        If True, returns a dict:
            {
                "results": [...],            # same list as before
                "operation_summary": {...}   # new field, additive only
            }
    """
    structure = ArrayWithRangeSum(initial, track_summary=include_summary)
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

    if not include_summary:
        return results
    return {
        "results": results,
        "operation_summary": structure.summary(),
    }


if __name__ == "__main__":
    base_array = [1, 3, 5, 7, 9, 11]
    ops = [
        ("query", 1, 3),
        ("update", 1, 10),
        ("query", 1, 3),
        ("update", 4, 0),
        ("query", 0, 5),
        ("query", 2, 2),
    ]

    # Feature disabled: original contract unchanged
    plain = process_operations(base_array, ops)
    assert plain == [15, 22, 34, 5], f"Original contract broken: {plain}"

    # Feature enabled: additive field, same results
    full = process_operations(base_array, ops, include_summary=True)
    assert full["results"] == [15, 22, 34, 5]
    assert full["operation_summary"]["updates_processed"] == 2
    assert full["operation_summary"]["queries_processed"] == 4
    assert full["operation_summary"]["total_fenwick_node_touches"] == (
        full["operation_summary"]["fenwick_update_node_touches"]
        + full["operation_summary"]["fenwick_query_node_touches"]
    )

    print("All tests passed.")
    print(full)