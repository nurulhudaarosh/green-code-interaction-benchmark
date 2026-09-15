class FenwickTree:
    """1-indexed Binary Indexed Tree (Fenwick Tree) for dynamic range prefix sums."""
    def __init__(self, size: int):
        self.n = size
        self.tree = [0] * (size + 1)

    def add(self, idx: int, delta: int) -> None:
        """Adds delta to the element at 1-based index `idx`."""
        while idx <= self.n:
            self.tree[idx] += delta
            idx += idx & (-idx)

    def query(self, idx: int) -> int:
        """Returns the prefix sum from 1 to 1-based index `idx` inclusive."""
        total = 0
        while idx > 0:
            total += self.tree[idx]
            idx -= idx & (-idx)
        return total


class DynamicArrayRangeSum:
    def __init__(self, nums: list[int]):
        self.nums = list(nums)
        self.n = len(nums)
        self.bit = FenwickTree(self.n)
        
        # Build the Fenwick Tree in O(N) time
        for i in range(1, self.n + 1):
            self.bit.tree[i] += self.nums[i - 1]
            parent = i + (i & (-i))
            if parent <= self.n:
                self.bit.tree[parent] += self.bit.tree[i]

    def update(self, index: int, val: int) -> None:
        """Replaces the element at 0-based `index` with `val`."""
        delta = val - self.nums[index]
        self.nums[index] = val
        self.bit.add(index + 1, delta)

    def query_range(self, left: int, right: int) -> int:
        """Returns the sum of elements from 0-based indices `left` to `right` inclusive."""
        if left > right:
            return 0
        return self.bit.query(right + 1) - self.bit.query(left)


def process_operations(nums: list[int], operations: list[tuple]) -> list[int]:
    """
    Processes operations and returns query results in order.
    
    Operations format:
    - ('UPDATE', index, new_val) -> Point replacement
    - ('QUERY', left, right)    -> Inclusive range sum
    """
    ds = DynamicArrayRangeSum(nums)
    results = []
    
    for op in operations:
        if op[0] == 'UPDATE':
            _, idx, val = op
            ds.update(idx, val)
        elif op[0] == 'QUERY':
            _, left, right = op
            results.append(ds.query_range(left, right))
            
    return results


# Example Usage
if __name__ == "__main__":
    initial_array = [1, 3, 5, 7, 9, 11]
    ops = [
        ('QUERY', 1, 3),    # sum(nums[1..3]) = 3 + 5 + 7 = 15
        ('UPDATE', 1, 10),   # nums[1] becomes 10
        ('QUERY', 1, 3),    # sum(nums[1..3]) = 10 + 5 + 7 = 22
        ('QUERY', 0, 5),    # sum(nums[0..5]) = 1 + 10 + 5 + 7 + 9 + 11 = 43
    ]
    
    output = process_operations(initial_array, ops)
    print("Query Results:", output)  # Expected: [15, 22, 43]