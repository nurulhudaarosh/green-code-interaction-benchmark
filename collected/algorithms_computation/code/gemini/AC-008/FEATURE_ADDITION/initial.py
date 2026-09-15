class FenwickTree:
    def __init__(self, size: int):
        self.n = size
        self.tree = [0] * (size + 1)

    def add(self, index: int, delta: int) -> None:
        """Adds delta to 1-based index."""
        i = index
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def query(self, index: int) -> int:
        """Returns prefix sum from 1 to index (inclusive)."""
        s = 0
        i = index
        while i > 0:
            s += self.tree[i]
            i -= i & -i
        return s


class NumArray:
    def __init__(self, nums: list[int]):
        self.nums = list(nums)
        self.n = len(nums)
        self.bit = FenwickTree(self.n)
        for i, val in enumerate(self.nums):
            self.bit.add(i + 1, val)

    def update(self, index: int, val: int) -> None:
        """Point replacement: set nums[index] = val."""
        delta = val - self.nums[index]
        self.nums[index] = val
        self.bit.add(index + 1, delta)

    def sum_range(self, left: int, right: int) -> int:
        """Returns inclusive range sum from left to right."""
        return self.bit.query(right + 1) - self.bit.query(left)


def process_operations(nums: list[int], operations: list[tuple]) -> list[int]:
    """
    Executes a sequence of operations.
    Operations format:
      - ("update", index, val)
      - ("query", left, right)
    Returns list of query results.
    """
    ds = NumArray(nums)
    results = []
    for op in operations:
        if op[0] == "update":
            _, idx, val = op
            ds.update(idx, val)
        elif op[0] == "query":
            _, left, right = op
            results.append(ds.sum_range(left, right))
    return results


# Example Usage
if __name__ == "__main__":
    arr = [1, 3, 5]
    ops = [
        ("query", 0, 2),  # sum(1, 3, 5) = 9
        ("update", 1, 2), # arr becomes [1, 2, 5]
        ("query", 0, 2),  # sum(1, 2, 5) = 8
    ]
    print("Query Results:", process_operations(arr, ops))