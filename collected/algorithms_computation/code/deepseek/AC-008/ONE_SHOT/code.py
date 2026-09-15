class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)
    
    def build(self, arr):
        """Build Fenwick tree from array (1-indexed internally)"""
        for i in range(1, self.n + 1):
            self.bit[i] += arr[i - 1]
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]
    
    def update(self, idx, delta):
        """Add delta to position idx (0-indexed)"""
        i = idx + 1  # convert to 1-indexed
        while i <= self.n:
            self.bit[i] += delta
            i += i & -i
    
    def prefix_sum(self, idx):
        """Sum of elements from 0 to idx (inclusive), idx is 0-indexed"""
        if idx < 0:
            return 0
        i = idx + 1  # convert to 1-indexed
        result = 0
        while i > 0:
            result += self.bit[i]
            i -= i & -i
        return result
    
    def range_sum(self, left, right):
        """Sum of elements from left to right (inclusive), both 0-indexed"""
        if left > right:
            return 0
        return self.prefix_sum(right) - self.prefix_sum(left - 1)


def solve():
    """
    Reads input from stdin in the following format:
    First line: n q (size of array, number of operations)
    Second line: n integers (initial array)
    Next q lines: operations
        - "update idx val" : set arr[idx] = val (0-indexed)
        - "query l r" : return sum of arr[l..r] (inclusive, 0-indexed)
    """
    import sys
    
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    it = iter(data)
    n = int(next(it))
    q = int(next(it))
    
    arr = [int(next(it)) for _ in range(n)]
    
    fenwick = FenwickTree(n)
    fenwick.build(arr)
    
    results = []
    
    for _ in range(q):
        op = next(it)
        if op == "update":
            idx = int(next(it))
            val = int(next(it))
            delta = val - arr[idx]
            arr[idx] = val
            fenwick.update(idx, delta)
        elif op == "query":
            l = int(next(it))
            r = int(next(it))
            results.append(str(fenwick.range_sum(l, r)))
    
    sys.stdout.write("\n".join(results))


if __name__ == "__main__":
    solve()