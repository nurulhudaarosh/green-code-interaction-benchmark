class FenwickTree:
    """1-indexed Binary Indexed Tree (Fenwick Tree) with O(N) initialization and O(log N) updates/queries."""
    def __init__(self, size: int):
        self.n = size
        self.tree = [0] * (size + 1)

    def add(self, idx: int, delta: int) -> None:
        """Adds delta to 1-based index `idx`. Traverses upwards using lower bit (i += i & -i)."""
        while idx <= self.n:
            self.tree[idx] += delta
            idx += idx & (-idx)

    def query(self, idx: int) -> int:
        """Computes prefix sum from 1 to 1-based index `idx`. Traverses downwards using lower bit (i -= i & -i)."""
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
        
        # O(N) linear build for Fenwick Tree
        for i in range(1, self.n + 1):
            self.bit.tree[i] += self.nums[i - 1]
            parent = i + (i & (-i))
            if parent <= self.n:
                self.bit.tree[parent] += self.bit.tree[i]

    def update(self, index: int, val: int) -> None:
        """Replaces element at 0-based `index` with `val`."""
        delta = val - self.nums[index]
        self.nums[index] = val
        self.bit.add(index + 1, delta)

    def query_range(self, left: int, right: int) -> int:
        """Returns sum of elements from 0-based indices `left` to `right` inclusive."""
        if left > right or left < 0 or right >= self.n:
            return 0
        return self.bit.query(right + 1) - self.bit.query(left)


def process_operations(nums: list[int], operations: list[tuple]) -> list[int]:
    """Processes 'UPDATE' and 'QUERY' operations and returns results preserving output order."""
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


# ---------------------------------------------------------
# Verification & Hard-Case Test Suite
# ---------------------------------------------------------

def run_tests():
    # Test 1: Original Example
    initial_array = [1, 3, 5, 7, 9, 11]
    ops = [
        ('QUERY', 1, 3),    # 3 + 5 + 7 = 15
        ('UPDATE', 1, 10),   # nums[1] becomes 10
        ('QUERY', 1, 3),    # 10 + 5 + 7 = 22
        ('QUERY', 0, 5),    # 1 + 10 + 5 + 7 + 9 + 11 = 43
    ]
    assert process_operations(initial_array, ops) == [15, 22, 43], "Failed Original Example"

    # Test 2: Maximum Traversal Depth (Worst-Case Bit-Flip Pattern N = 2^k - 1)
    N = (1 << 15) - 1  # 32767 elements (0b111111111111111)
    large_nums = [1] * N
    worst_case_ops = [
        # Querying N requires clearing all 15 set bits in binary
        ('QUERY', 0, N - 1),
        # Point update at index N-1 triggers max upward bit propagation
        ('UPDATE', N - 1, 100),
        ('QUERY', 0, N - 1),
        ('QUERY', N - 1, N - 1)
    ]
    expected_worst = [N, N - 1 + 100, 100]
    assert process_operations(large_nums, worst_case_ops) == expected_worst, "Failed Worst-Case Structure Test"

    # Test 3: Edge Cases (Single element, Range L == R, Zero Range, Large Integers)
    single_num = [10**18]
    edge_ops = [
        ('QUERY', 0, 0),
        ('UPDATE', 0, -10**18),
        ('QUERY', 0, 0),
    ]
    assert process_operations(single_num, edge_ops) == [10**18, -10**18], "Failed Edge Cases"

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()