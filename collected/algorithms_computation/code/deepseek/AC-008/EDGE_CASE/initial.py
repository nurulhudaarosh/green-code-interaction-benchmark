class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)
    
    def build(self, arr):
        # Build the Fenwick tree from an array in O(n)
        for i in range(1, self.n + 1):
            self.bit[i] += arr[i - 1]
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]
    
    def update(self, idx, delta):
        # Add delta to the element at index idx (1-based)
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & -idx
    
    def prefix_sum(self, idx):
        # Sum of elements from 1 to idx (1-based)
        result = 0
        while idx > 0:
            result += self.bit[idx]
            idx -= idx & -idx
        return result
    
    def range_sum(self, left, right):
        # Sum of elements from left to right (inclusive, 1-based)
        return self.prefix_sum(right) - self.prefix_sum(left - 1)


def solve():
    import sys
    input_data = sys.stdin.read().strip().split()
    if not input_data:
        return
    
    it = iter(input_data)
    n = int(next(it))
    q = int(next(it))
    
    arr = [int(next(it)) for _ in range(n)]
    
    ft = FenwickTree(n)
    ft.build(arr)
    
    results = []
    
    for _ in range(q):
        typ = int(next(it))
        if typ == 1:
            # Point update: add value to position pos (1-based)
            pos = int(next(it))
            val = int(next(it))
            ft.update(pos, val)
        else:
            # Range sum query: inclusive range [l, r]
            l = int(next(it))
            r = int(next(it))
            results.append(str(ft.range_sum(l, r)))
    
    sys.stdout.write("\n".join(results))


if __name__ == "__main__":
    solve()