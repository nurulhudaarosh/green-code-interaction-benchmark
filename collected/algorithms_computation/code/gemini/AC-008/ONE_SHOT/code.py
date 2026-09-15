class FenwickTree:
    def __init__(self, size: int):
        self.n = size
        self.tree = [0] * (self.n + 1)

    def update(self, idx: int, delta: int) -> None:
        """Adds delta to the element at 1-based index idx."""
        while idx <= self.n:
            self.tree[idx] += delta
            idx += idx & -idx

    def query(self, idx: int) -> int:
        """Returns the prefix sum from index 1 to idx (inclusive)."""
        s = 0
        while idx > 0:
            s += self.tree[idx]
            idx -= idx & -idx
        return s

    def range_query(self, left: int, right: int) -> int:
        """Returns the sum in inclusive range [left, right] (1-based indices)."""
        return self.query(right) - self.query(left - 1)


class PointUpdateRangeSumArray:
    def __init__(self, nums: list[int]):
        """Initializes the array with 0-based indexing."""
        self.n = len(nums)
        self.nums = list(nums)
        self.bit = FenwickTree(self.n)
        
        # Build Fenwick Tree in O(N) time
        for i in range(1, self.n + 1):
            self.bit.tree[i] += self.nums[i - 1]
            parent = i + (i & -i)
            if parent <= self.n:
                self.bit.tree[parent] += self.bit.tree[i]

    def update(self, index: int, val: int) -> None:
        """Point replacement operation: Sets nums[index] = val (0-based index)."""
        delta = val - self.nums[index]
        self.nums[index] = val
        self.bit.update(index + 1, delta)

    def sum_range(self, left: int, right: int) -> int:
        """Inclusive range-sum query in range [left, right] (0-based index)."""
        return self.bit.range_query(left + 1, right + 1)


def process_queries(nums: list[int], operations: list[tuple]) -> list[int]:
    """
    Processes operations and returns query results in order.
    
    Operations format:
    - ("update", index, val) -> Point replacement
    - ("query", left, right) -> Inclusive range-sum query
    """
    arr = PointUpdateRangeSumArray(nums)
    results = []
    
    for op in operations:
        if op[0] == "update":
            _, idx, val = op
            arr.update(idx, val)
        elif op[0] == "query":
            _, left, right = op
            results.append(arr.sum_range(left, right))
            
    return results


# Example Usage
if __name__ == "__main__":
    initial_nums = [1, 3, 5, 7, 9, 11]
    ops = [
        ("query", 1, 3),   # Sum of [3, 5, 7] = 15
        ("update", 1, 10), # Set index 1 to 10 (array is now [1, 10, 5, 7, 9, 11])
        ("query", 1, 3),   # Sum of [10, 5, 7] = 22
        ("query", 0, 5)    # Total sum = 43
    ]
    
    output = process_queries(initial_nums, ops)
    print("Query Results:", output)  # Expected: [15, 22, 43]