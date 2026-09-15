class FenwickTree:
    def __init__(self, arr: list[int]):
        """Initializes Fenwick tree from a 0-indexed array in O(N) time."""
        self.n = len(arr)
        self.arr = list(arr)
        self.tree = [0] * (self.n + 1)
        
        for i in range(1, self.n + 1):
            self.tree[i] += self.arr[i - 1]
            parent = i + (i & (-i))
            if parent <= self.n:
                self.tree[parent] += self.tree[i]

    def update(self, index: int, val: int) -> None:
        """Sets the value at 0-based index to val."""
        delta = val - self.arr[index]
        self.arr[index] = val
        
        idx = index + 1
        while idx <= self.n:
            self.tree[idx] += delta
            idx += idx & (-idx)

    def _prefix_sum(self, idx: int) -> int:
        """Calculates sum from index 1 to 1-based index idx."""
        s = 0
        while idx > 0:
            s += self.tree[idx]
            idx -= idx & (-idx)
        return s

    def sum_range(self, left: int, right: int) -> int:
        """Returns the inclusive range sum from 0-based indices [left, right]."""
        if left > right:
            return 0
        return self._prefix_sum(right + 1) - self._prefix_sum(left)


def process_queries(arr: list[int], queries: list[tuple]) -> list[int]:
    """
    Processes operations on an array:
      - ('update', index, val): Replaces arr[index] with val
      - ('query', left, right): Computes sum in inclusive range [left, right]
    Returns list of results for 'query' operations in order.
    """
    bit = FenwickTree(arr)
    results = []
    
    for op in queries:
        if op[0] == 'update':
            bit.update(op[1], op[2])
        elif op[0] == 'query':
            results.append(bit.sum_range(op[1], op[2]))
            
    return results


# Example Usage
if __name__ == "__main__":
    initial_array = [1, 3, 5, 7, 9, 11]
    operations = [
        ('query', 1, 3),   # arr[1..3] -> 3 + 5 + 7 = 15
        ('update', 1, 10), # set arr[1] = 10
        ('query', 1, 3),   # arr[1..3] -> 10 + 5 + 7 = 22
        ('query', 0, 5),   # sum of all elements -> 43
    ]
    
    print(process_queries(initial_array, operations))