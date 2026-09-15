"""
Fenwick Tree (Binary Indexed Tree) for point-update / range-sum queries.

Problem
-------
Maintain an integer array under two operations:
  1. Point replacement: set a[i] = v
  2. Range sum query (inclusive): sum of a[l..r]
Return each query result, in the order the queries occur.

Key constraints
----------------
- Array is 0-indexed, size n.
- Updates REPLACE the value at an index (not add to it).
- Queries are inclusive on both ends: 0 <= l <= r <= n-1.
- Must support many operations efficiently: O(log n) per update/query,
  not O(n) naive recomputation.

Required output
----------------
A list of integers: the result of each query, in call order.

Algorithm
---------
A Fenwick tree (BIT) stores partial sums indexed by the binary
representation of positions:
  - update: add a delta at index i, walking up the tree (i += i & -i) -> O(log n)
  - prefix_sum(i): sum of a[0..i], walking down the tree (i -= i & -i) -> O(log n)
  - range_sum(l, r) = prefix_sum(r) - prefix_sum(l-1)
Since operations here are replacements, each update is converted to a
delta (new_value - old_value) before being applied to the tree, and the
current value is tracked separately for the next delta computation.

This implementation uses only the standard library, has no randomness,
no I/O side effects beyond print in the demo, and is fully deterministic.
"""

from typing import List, Tuple, Union


class FenwickArray:
    """Array supporting point updates and inclusive range-sum queries."""

    def __init__(self, initial: List[int]):
        self.n = len(initial)
        self._values = list(initial)          # current array values (0-indexed)
        self._tree = [0] * (self.n + 1)        # Fenwick tree storage, 1-indexed
        for i, v in enumerate(initial):
            self._add(i, v)

    def _add(self, index: int, delta: int) -> None:
        i = index + 1
        while i <= self.n:
            self._tree[i] += delta
            i += i & (-i)

    def _prefix_sum(self, index: int) -> int:
        if index < 0:
            return 0
        i = index + 1
        s = 0
        while i > 0:
            s += self._tree[i]
            i -= i & (-i)
        return s

    def update(self, index: int, value: int) -> None:
        """Point replacement: set a[index] = value."""
        if not (0 <= index < self.n):
            raise IndexError(f"update index {index} out of range [0, {self.n - 1}]")
        delta = value - self._values[index]
        if delta != 0:
            self._add(index, delta)
            self._values[index] = value

    def query(self, left: int, right: int) -> int:
        """Inclusive range sum a[left..right]."""
        if not (0 <= left <= right < self.n):
            raise IndexError(f"query range [{left}, {right}] invalid for size {self.n}")
        return self._prefix_sum(right) - self._prefix_sum(left - 1)


Operation = Union[Tuple[str, int, int]]


def process_operations(initial: List[int], operations: List[Operation]) -> List[int]:
    """
    Apply a sequence of operations and return query results in order.

    Each operation is a tuple:
        ("update", index, value)  -> set a[index] = value
        ("query",  left, right)   -> record sum(a[left..right]) inclusive
    """
    fenwick = FenwickArray(initial)
    results: List[int] = []

    for op in operations:
        kind = op[0]
        if kind == "update":
            _, index, value = op
            fenwick.update(index, value)
        elif kind == "query":
            _, left, right = op
            results.append(fenwick.query(left, right))
        else:
            raise ValueError(f"Unknown operation type: {kind!r}")

    return results


def _self_test() -> None:
    """Deterministic checks against a brute-force reference implementation."""

    def brute_force(initial: List[int], operations: List[Operation]) -> List[int]:
        a = list(initial)
        out = []
        for op in operations:
            kind = op[0]
            if kind == "update":
                _, i, v = op
                a[i] = v
            elif kind == "query":
                _, l, r = op
                out.append(sum(a[l:r + 1]))
        return out

    test_cases = [
        (
            [1, 2, 3, 4, 5],
            [
                ("query", 0, 4),
                ("query", 1, 3),
                ("update", 2, 10),
                ("query", 0, 4),
                ("query", 2, 2),
                ("update", 0, -5),
                ("query", 0, 1),
            ],
        ),
        (
            [0, 0, 0, 0],
            [
                ("query", 0, 3),
                ("update", 0, 1),
                ("update", 1, 2),
                ("update", 2, 3),
                ("update", 3, 4),
                ("query", 0, 3),
                ("query", 1, 2),
            ],
        ),
        (
            [7],
            [
                ("query", 0, 0),
                ("update", 0, -7),
                ("query", 0, 0),
            ],
        ),
    ]

    for idx, (initial, ops) in enumerate(test_cases):
        expected = brute_force(initial, ops)
        actual = process_operations(initial, ops)
        assert actual == expected, f"Test case {idx} failed: expected {expected}, got {actual}"

    print("All self-tests passed.")


if __name__ == "__main__":
    _self_test()

    initial_array = [1, 2, 3, 4, 5]
    ops = [
        ("query", 0, 4),
        ("update", 2, 10),
        ("query", 0, 4),
        ("query", 1, 2),
    ]
    print("Query results:", process_operations(initial_array, ops))