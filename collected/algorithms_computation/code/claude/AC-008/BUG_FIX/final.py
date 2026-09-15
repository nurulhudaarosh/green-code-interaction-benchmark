"""
Point-update / range-sum-query maintenance using a Fenwick tree (BIT).

Determinism rule: operations are applied strictly in their given sequence
order. The position of an operation in the `operations` list IS its
tie-break key -- when multiple operations target the same index, the one
later in the list always wins. Callers must supply a genuine ordered
sequence (list/tuple), never a set or dict (which have no reliable order
guarantee for this purpose); passing one raises TypeError.
"""

from typing import List, Sequence, Tuple, Union


class FenwickTree:
    def __init__(self, n: int) -> None:
        self.n = n
        self.tree = [0] * (n + 1)

    def _add(self, i: int, delta: int) -> None:
        i += 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & (-i)

    def _prefix_sum(self, i: int) -> int:
        if i < 0:
            return 0
        i += 1
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & (-i)
        return s

    def range_sum(self, l: int, r: int) -> int:
        return self._prefix_sum(r) - self._prefix_sum(l - 1)

    def point_update(self, i: int, delta: int) -> None:
        self._add(i, delta)


class NumArray:
    def __init__(self, nums: List[int]) -> None:
        self.n = len(nums)
        self.arr = list(nums)
        self.bit = FenwickTree(self.n)
        for idx, v in enumerate(self.arr):
            self.bit.point_update(idx, v)  # always add, even v == 0, for consistency

    def update(self, index: int, val: int) -> None:
        if not (0 <= index < self.n):
            raise IndexError(f"update index {index} out of range [0, {self.n})")
        delta = val - self.arr[index]
        self.bit.point_update(index, delta)
        self.arr[index] = val

    def sum_range(self, left: int, right: int) -> int:
        if not (0 <= left <= right < self.n):
            raise IndexError(f"query range [{left}, {right}] invalid for size {self.n}")
        return self.bit.range_sum(left, right)


Operation = Tuple[str, int, int]


def process_operations(nums: List[int], operations: Sequence[Operation]) -> List[int]:
    if isinstance(operations, (set, frozenset, dict)):
        raise TypeError(
            "operations must be an ordered sequence (list/tuple); "
            "sets/dicts have no reliable order and break deterministic tie handling"
        )

    num_array = NumArray(nums)
    results: List[int] = []

    for op in operations:  # strict sequence order = the tie-break rule
        kind = op[0]
        if kind == "update":
            _, index, val = op
            num_array.update(index, val)
        elif kind == "query":
            _, left, right = op
            results.append(num_array.sum_range(left, right))
        else:
            raise ValueError(f"Unknown operation type: {kind!r}")

    return results


if __name__ == "__main__":
    nums = [5]
    ops_a = [("update", 0, 10), ("update", 0, 20), ("query", 0, 0)]
    ops_b = [("update", 0, 20), ("update", 0, 10), ("query", 0, 0)]
    print(process_operations(nums, ops_a))  # [20] -- last write in sequence wins
    print(process_operations(nums, ops_b))  # [10] -- deterministic per given order