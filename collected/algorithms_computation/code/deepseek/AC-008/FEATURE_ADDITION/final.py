class FenwickTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.bit = [0] * (self.n + 1)
        # Build in O(n)
        for i in range(1, self.n + 1):
            self.bit[i] += arr[i - 1]
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]

    def add(self, idx, delta):
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & -idx

    def prefix_sum(self, idx):
        s = 0
        while idx > 0:
            s += self.bit[idx]
            idx -= idx & -idx
        return s

    def range_sum(self, l, r):
        return self.prefix_sum(r) - self.prefix_sum(l - 1)


def process_operations(n, initial_array, operations, return_summary=False):
    """
    Process operations and return query results.
    
    Args:
        n: size of the array (len(initial_array) must equal n)
        initial_array: list of integers (0‑based internally, but problem uses 1‑based)
        operations: list of tuples, each either
            ('update', idx, new_val)   # idx is 1‑based
            ('query', l, r)            # l, r are 1‑based inclusive
        return_summary: bool, if True, include an 'operation_summary' field.
    
    Returns:
        If return_summary is False: list of integers (query results in order).
        If return_summary is True: dict with keys:
            'query_results': list of integers
            'operation_summary': int (total major decisions)
    """
    fenwick = FenwickTree(initial_array)
    current = initial_array[:]
    results = []
    
    # Count major computational decisions
    # Initial build: n decisions (one per element)
    major_decisions = n
    
    for op in operations:
        if op[0] == 'update':
            _, idx, new_val = op
            delta = new_val - current[idx - 1]
            fenwick.add(idx, delta)
            current[idx - 1] = new_val
            # One major decision: compute delta and apply update
            major_decisions += 1
        else:  # 'query'
            _, l, r = op
            results.append(fenwick.range_sum(l, r))
            # Two major decisions: two prefix‑sum traversals
            major_decisions += 2
    
    if return_summary:
        return {
            'query_results': results,
            'operation_summary': major_decisions
        }
    else:
        return results


# ========== Example usage ==========
if __name__ == "__main__":
    arr = [1, 3, 5, 7, 9]
    ops = [
        ('query', 2, 4),      # sum = 15
        ('update', 3, 10),    # set index 3 to 10
        ('query', 1, 5),      # sum = 30
        ('query', 3, 3)       # sum = 10
    ]
    
    # Original behaviour (no summary)
    print("Original output (no summary):")
    print(process_operations(len(arr), arr, ops, return_summary=False))
    # Expected: [15, 30, 10]
    
    # With summary enabled
    print("\nWith summary enabled:")
    result_with_summary = process_operations(len(arr), arr, ops, return_summary=True)
    print(result_with_summary)
    # Expected: {'query_results': [15, 30, 10], 'operation_summary': 5 (initial build) + 1*1 (update) + 3*2 (queries) = 12}
    # Breakdown: n=5 build, one update = 1, three queries = 3*2 = 6 → total = 5+1+6 = 12