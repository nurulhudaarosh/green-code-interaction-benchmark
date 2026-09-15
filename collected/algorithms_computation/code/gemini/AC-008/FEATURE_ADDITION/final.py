class FenwickTreeWithMetrics:
    def __init__(self, size: int):
        self.n = size
        self.tree = [0] * (size + 1)
        self.traversals = 0

    def add(self, index: int, delta: int) -> None:
        """Adds delta to 1-based index and tracks traversal steps."""
        i = index
        while i <= self.n:
            self.tree[i] += delta
            self.traversals += 1
            i += i & -i

    def query(self, index: int) -> int:
        """Returns prefix sum from 1 to index and tracks traversal steps."""
        s = 0
        i = index
        while i > 0:
            s += self.tree[i]
            self.traversals += 1
            i -= i & -i
        return s


class MutableRangeSumEngine:
    def __init__(self, nums: list[int]):
        self.nums = list(nums)
        self.n = len(nums)
        self.bit = FenwickTreeWithMetrics(self.n)
        for i, val in enumerate(self.nums):
            self.bit.add(i + 1, val)

    def update(self, index: int, val: int) -> None:
        delta = val - self.nums[index]
        self.nums[index] = val
        self.bit.add(index + 1, delta)

    def sum_range(self, left: int, right: int) -> int:
        return self.bit.query(right + 1) - self.bit.query(left)


def process_operations(
    nums: list[int], operations: list[tuple], return_summary: bool = False
) -> list[int] | dict:
    """
    Executes operations on the array.
    Operations format:
      - ("update", index, val)
      - ("query", left, right)
    """
    ds = MutableRangeSumEngine(nums)
    
    # Reset tree traversals to exclude initial construction overhead
    ds.bit.traversals = 0
    
    results = []
    updates_count = 0
    queries_count = 0

    for op in operations:
        if op[0] == "update":
            _, idx, val = op
            ds.update(idx, val)
            updates_count += 1
        elif op[0] == "query":
            _, left, right = op
            results.append(ds.sum_range(left, right))
            queries_count += 1

    if not return_summary:
        return results

    return {
        "results": results,
        "operation_summary": {
            "total_operations": len(operations),
            "point_updates": updates_count,
            "range_queries": queries_count,
            "tree_traversals": ds.bit.traversals,
        },
    }


# Example Usage
if __name__ == "__main__":
    arr = [1, 3, 5]
    ops = [
        ("query", 0, 2),  # sum = 9
        ("update", 1, 2), # arr = [1, 2, 5]
        ("query", 0, 2),  # sum = 8
    ]

    # Standard Output
    print("Standard Results:", process_operations(arr, ops))

    # Extended Output with operation_summary
    summary_output = process_operations(arr, ops, return_summary=True)
    print("\nWith Operation Summary:")
    print("Results:", summary_output["results"])
    print("Summary:", summary_output["operation_summary"])