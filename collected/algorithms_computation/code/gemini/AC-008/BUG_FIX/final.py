class FenwickTree:
    """A 1-indexed Fenwick Tree (Binary Indexed Tree) for prefix sums."""
    def __init__(self, size: int):
        self.n = size
        self.tree = [0] * (self.n + 1)

    @classmethod
    def build_from_array(cls, arr: list[int]) -> "FenwickTree":
        """Constructs a Fenwick Tree from an initial array in O(N) time."""
        n = len(arr)
        bit = cls(n)
        for i in range(1, n + 1):
            bit.tree[i] += arr[i - 1]
            parent = i + (i & -i)
            if parent <= n:
                bit.tree[parent] += bit.tree[i]
        return bit

    def add(self, index: int, delta: int) -> None:
        """Adds delta to the element at 1-based index in O(log N)."""
        while index <= self.n:
            self.tree[index] += delta
            index += index & -index

    def query(self, index: int) -> int:
        """Returns cumulative sum from index 1 to index (1-based) in O(log N)."""
        index = min(index, self.n)  # Cap at max size
        total = 0
        while index > 0:
            total += self.tree[index]
            index -= index & -index
        return total

    def range_query(self, left: int, right: int) -> int:
        """
        Calculates inclusive range sum [left, right] (1-based indices).
        Returns 0 deterministically if the range is invalid or left > right.
        """
        if left > right or right < 1 or left > self.n:
            return 0
        
        # Clamp bounds to valid [1, N] window
        left = max(1, left)
        right = min(self.n, right)
        
        return self.query(right) - self.query(left - 1)


def process_operations(arr: list[int], operations: list[tuple]) -> list[int]:
    """
    Processes dynamic point updates and range sum queries.
    
    Operations format:
      - ('update', index, val): Point replacement arr[index] = val
      - ('query', left, right): Inclusive range sum from left to right
    """
    n = len(arr)
    if n == 0:
        return [0 if op[0] == 'query' else None for op in operations if op[0] == 'query']

    # Initialize BIT in linear time O(N)
    bit = FenwickTree.build_from_array(arr)
    current_arr = list(arr)
    results = []

    for op in operations:
        op_type = op[0]
        
        if op_type == 'update':
            idx, new_val = op[1], op[2]
            if 0 <= idx < n:
                delta = new_val - current_arr[idx]
                current_arr[idx] = new_val
                bit.add(idx + 1, delta)  # Convert 0-based to 1-based index
                
        elif op_type == 'query':
            left, right = op[1], op[2]
            # Convert 0-based input indices to 1-based for internal Fenwick tree
            res = bit.range_query(left + 1, right + 1)
            results.append(res)

    return results


# Verification
if __name__ == "__main__":
    initial_array = [1, 3, 5, 7, 9, 11]
    queries = [
        ('query', 1, 3),    # 3 + 5 + 7 = 15
        ('update', 1, 10),  # arr becomes [1, 10, 5, 7, 9, 11]
        ('query', 1, 3),    # 10 + 5 + 7 = 22
        ('query', 3, 1),    # Invalid range (left > right) -> 0
        ('query', -2, 2),   # Out-of-bounds left clamped -> arr[0..2] = 1 + 10 + 5 = 16
    ]

    output = process_operations(initial_array, queries)
    print("Execution Output:", output)  # [15, 22, 0, 16]