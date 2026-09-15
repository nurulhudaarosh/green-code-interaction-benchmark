class FenwickTree:
    def __init__(self, size: int):
        self.n = size
        self.tree = [0] * (self.n + 1)

    def add(self, index: int, delta: int) -> None:
        """Adds delta to the element at 1-based index."""
        while index <= self.n:
            self.tree[index] += delta
            index += index & -index

    def query(self, index: int) -> int:
        """Returns the sum of elements from 1 to 1-based index."""
        total = 0
        while index > 0:
            total += self.tree[index]
            index -= index & -index
        return total

    def range_query(self, left: int, right: int) -> int:
        """Returns the sum of elements in inclusive range [left, right] (1-based)."""
        if left > right:
            return 0
        return self.query(right) - self.query(left - 1)


def process_operations(arr: list[int], operations: list[tuple]) -> list[int]:
    """
    Processes point updates and range sum queries on an array.
    
    Operations format:
      - ('update', index, val): Replaces arr[index] with val (0-based indexing)
      - ('query', left, right): Range sum from left to right inclusive (0-based indexing)
    """
    n = len(arr)
    bit = FenwickTree(n)
    
    # Store a copy of the array to compute replacement deltas
    current_arr = list(arr)
    
    # Initialize the Fenwick tree
    for idx, val in enumerate(arr, start=1):
        bit.add(idx, val)
        
    results = []
    
    for op in operations:
        op_type = op[0]
        if op_type == 'update':
            idx, new_val = op[1], op[2]
            delta = new_val - current_arr[idx]
            current_arr[idx] = new_val
            bit.add(idx + 1, delta)  # Convert to 1-based index
            
        elif op_type == 'query':
            left, right = op[1], op[2]
            res = bit.range_query(left + 1, right + 1)  # Convert to 1-based index
            results.append(res)
            
    return results


# Example Usage
if __name__ == "__main__":
    initial_array = [1, 3, 5, 7, 9, 11]
    queries = [
        ('query', 1, 3),   # Sum of arr[1..3] -> 3 + 5 + 7 = 15
        ('update', 1, 10), # Set arr[1] = 10 (array is now [1, 10, 5, 7, 9, 11])
        ('query', 1, 3),   # Sum of arr[1..3] -> 10 + 5 + 7 = 22
        ('query', 0, 5),   # Sum of arr[0..5] -> 1 + 10 + 5 + 7 + 9 + 11 = 43
    ]

    output = process_operations(initial_array, queries)
    print("Query Results:", output)