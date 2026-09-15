class FenwickTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.bit = [0] * (self.n + 1)
        # Build in O(n) for efficiency
        for i in range(1, self.n + 1):
            self.bit[i] += arr[i - 1]
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]

    def add(self, idx, delta):
        # idx is 1-based
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & -idx

    def prefix_sum(self, idx):
        # sum from 1 to idx inclusive
        s = 0
        while idx > 0:
            s += self.bit[idx]
            idx -= idx & -idx
        return s

    def range_sum(self, l, r):
        return self.prefix_sum(r) - self.prefix_sum(l - 1)


def process_operations(n, initial_array, operations):
    """
    operations: list of tuples
        - ('update', index, new_value)  (index is 1-based)
        - ('query', l, r)               (l and r are 1-based inclusive)
    Returns: list of integers (results of queries in order)
    """
    fenwick = FenwickTree(initial_array)
    current = initial_array[:]   # keep a copy for delta calculation
    results = []

    for op in operations:
        if op[0] == 'update':
            _, idx, new_val = op
            delta = new_val - current[idx - 1]  # convert to 0-based internally
            fenwick.add(idx, delta)
            current[idx - 1] = new_val
        else:  # 'query'
            _, l, r = op
            results.append(fenwick.range_sum(l, r))

    return results


# === Example usage ===
if __name__ == "__main__":
    # Example: array of size 5, initial values [1, 3, 5, 7, 9]
    arr = [1, 3, 5, 7, 9]
    ops = [
        ('query', 2, 4),      # sum of indices 2..4 = 3+5+7 = 15
        ('update', 3, 10),    # set index 3 to 10
        ('query', 1, 5),      # sum = 1+3+10+7+9 = 30
        ('query', 3, 3)       # sum = 10
    ]
    output = process_operations(len(arr), arr, ops)
    print(output)  # Expected: [15, 30, 10]