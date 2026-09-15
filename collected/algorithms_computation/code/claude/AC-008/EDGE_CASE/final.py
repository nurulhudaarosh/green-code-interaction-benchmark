"""
Fenwick Tree (Binary Indexed Tree) for point updates and inclusive
range-sum queries.

Problem:
    Maintain an integer array under:
      1. Update  - point replacement: set a[i] = v
      2. Query   - inclusive range sum: sum(a[l..r])
    Return the result of each query, in the order the queries occur.

Key constraints:
    - n (array size) and q (number of operations) may be large, so each
      operation must run faster than O(n).
    - Updates replace a value (not increment it) - must be converted to
      a delta for the Fenwick tree.
    - Queries are inclusive on both ends (l and r included).

Required output:
    A list of integers, one per query, in input order. No tie-breaking
    rules apply - each query deterministically maps to one sum.

Algorithm:
    A Fenwick tree (Binary Indexed Tree) supports point updates and
    prefix-sum queries in O(log n) each, by walking indices via their
    lowest set bit (i & -i). A range sum [l, r] is prefix(r) - prefix(l-1).
    Total complexity: O((n + q) log n).

Worst-case-like structures explicitly handled and tested below:
    - Power-of-two sized arrays (maximal bit-traversal depth)
    - Off-by-one power-of-two sizes (n-1 of a power of two)
    - Repeated updates to boundary indices (0 and n-1)
    - Long alternating update/full-range-query chains
    - Repeated overwrite with the same value (zero-delta updates)
    - Degenerate n=1 arrays and single-element ranges (l == r)

Deterministic: no randomness, no I/O, no network access, no external
dependencies (standard library only).
"""

from typing import List, Sequence, Tuple


class FenwickTree:
    """1-indexed Fenwick tree storing point values, supporting prefix sums."""

    def __init__(self, values: Sequence[int]):
        self.n = len(values)
        self.tree = [0] * (self.n + 1)      # tree[1..n], tree[0] unused
        self.current = [0] * self.n         # current value at each 0-indexed pos

        for idx, val in enumerate(values):
            self.current[idx] = val

        # O(n) build: each position pushes its value to its immediate parent.
        for i in range(1, self.n + 1):
            self.tree[i] += self.current[i - 1]
            parent = i + (i & -i)
            if parent <= self.n:
                self.tree[parent] += self.tree[i]

    def _add(self, i: int, delta: int) -> None:
        """Add delta to 1-indexed position i."""
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def _prefix_sum(self, i: int) -> int:
        """Sum of the first i elements (1-indexed i), i.e. a[0..i-1]."""
        total = 0
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total

    def update(self, index: int, value: int) -> None:
        """Set a[index] = value (0-indexed)."""
        if not (0 <= index < self.n):
            raise IndexError(f"index {index} out of range [0, {self.n - 1}]")
        delta = value - self.current[index]
        if delta != 0:
            self.current[index] = value
            self._add(index + 1, delta)

    def range_sum(self, left: int, right: int) -> int:
        """Return sum(a[left..right]) inclusive, 0-indexed."""
        if not (0 <= left <= right < self.n):
            raise IndexError(f"invalid range [{left}, {right}] for size {self.n}")
        return self._prefix_sum(right + 1) - self._prefix_sum(left)


def process_operations(
    initial: Sequence[int],
    operations: Sequence[Tuple],
) -> List[int]:
    """
    Apply a sequence of operations to `initial` and return query results in order.

    Each operation is one of:
        ("update", index, value)
        ("query", left, right)

    Returns:
        List of integers: the result of each "query" operation, in order.
    """
    fenwick = FenwickTree(initial)
    results: List[int] = []

    for op in operations:
        kind = op[0]
        if kind == "update":
            _, index, value = op
            fenwick.update(index, value)
        elif kind == "query":
            _, left, right = op
            results.append(fenwick.range_sum(left, right))
        else:
            raise ValueError(f"Unknown operation: {op!r}")

    return results


def _naive_reference(initial: Sequence[int], operations: Sequence[Tuple]) -> List[int]:
    """O(n) per-operation reference implementation, used only for testing."""
    arr = list(initial)
    results: List[int] = []
    for op in operations:
        if op[0] == "update":
            _, idx, val = op
            arr[idx] = val
        else:
            _, l, r = op
            results.append(sum(arr[l : r + 1]))
    return results


def run_tests() -> None:
    """Deterministic tests, including worst-case-like structures."""

    # --- Test 1: basic sanity (small array, mixed ops) ---
    initial = [1, 3, 5, 7, 9, 11]
    ops = [
        ("query", 0, 5),
        ("update", 2, 100),
        ("query", 0, 5),
        ("query", 1, 3),
        ("update", 0, 0),
        ("query", 0, 0),
    ]
    assert process_operations(initial, ops) == _naive_reference(initial, ops)

    # --- Test 2: power-of-two sized array (maximal bit-traversal depth) ---
    n = 1024
    initial = list(range(n))
    ops = []
    for i in range(0, n, 37):          # scattered updates
        ops.append(("update", i, -i))
    ops.append(("query", 0, n - 1))    # full-range query
    ops.append(("query", 0, 511))
    ops.append(("query", 512, n - 1))
    assert process_operations(initial, ops) == _naive_reference(initial, ops)

    # --- Test 3: off-by-one power-of-two size (n - 1 = 1023) ---
    n = 1023
    initial = [1] * n
    ops = [("update", i, i) for i in range(0, n, 13)]
    ops += [("query", 0, n - 1), ("query", 100, 900)]
    assert process_operations(initial, ops) == _naive_reference(initial, ops)

    # --- Test 4: repeated updates to boundary indices (0 and n-1) ---
    n = 256
    initial = [0] * n
    ops = []
    for v in range(50):
        ops.append(("update", 0, v))
        ops.append(("update", n - 1, -v))
        ops.append(("query", 0, n - 1))
    assert process_operations(initial, ops) == _naive_reference(initial, ops)

    # --- Test 5: long alternating update / full-range-query chain ---
    n = 500
    initial = list(range(n))
    ops = []
    for i in range(n):
        ops.append(("update", i, i * i))
        ops.append(("query", 0, n - 1))
    assert process_operations(initial, ops) == _naive_reference(initial, ops)

    # --- Test 6: repeated overwrite with the same value (zero-delta path) ---
    initial = [5, 5, 5, 5, 5]
    ops = [
        ("update", 2, 5),   # no-op delta
        ("query", 0, 4),
        ("update", 2, 5),   # no-op delta again
        ("query", 2, 2),
    ]
    assert process_operations(initial, ops) == _naive_reference(initial, ops)
    assert process_operations(initial, ops) == [25, 5]

    # --- Test 7: degenerate n = 1 array and single-element ranges ---
    initial = [42]
    ops = [
        ("query", 0, 0),
        ("update", 0, -7),
        ("query", 0, 0),
    ]
    assert process_operations(initial, ops) == _naive_reference(initial, ops)
    assert process_operations(initial, ops) == [42, -7]

    # --- Test 8: single-element ranges (l == r) scattered across a larger array ---
    n = 50
    initial = list(range(n))
    ops = [("query", i, i) for i in range(n)]
    assert process_operations(initial, ops) == list(initial)  # each query returns a[i]

    print("All tests passed.")


if __name__ == "__main__":
    run_tests()

    # Original demonstration, output format unchanged.
    initial_array = [1, 3, 5, 7, 9, 11]
    ops = [
        ("query", 0, 5),
        ("update", 2, 100),
        ("query", 0, 5),
        ("query", 1, 3),
        ("update", 0, 0),
        ("query", 0, 0),
    ]
    output = process_operations(initial_array, ops)
    print("Query results:", output)