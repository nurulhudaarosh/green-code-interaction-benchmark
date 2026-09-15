import sys

class Fenwick:
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (self.n + 1)
        # Build tree in O(n) using linear construction
        for i, val in enumerate(arr, 1):
            self.tree[i] += val
            j = i + (i & -i)
            if j <= self.n:
                self.tree[j] += self.tree[i]

    def update(self, idx, delta):
        # idx is 0-based, convert to 1-based
        i = idx + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, idx):
        # idx is 0-based index (inclusive), return sum[0..idx]
        if idx < 0:
            return 0
        i = idx + 1
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i
        return s

    def range_sum(self, l, r):
        # inclusive, 0-based
        return self.prefix_sum(r) - self.prefix_sum(l - 1)


def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    it = iter(data)
    n = int(next(it))
    arr = [int(next(it)) for _ in range(n)]
    fenwick = Fenwick(arr)
    
    q = int(next(it))
    results = []
    for _ in range(q):
        typ = int(next(it))
        if typ == 0:  # point replacement: 0 i new_val
            i = int(next(it))
            new_val = int(next(it))
            delta = new_val - arr[i]
            arr[i] = new_val
            fenwick.update(i, delta)
        else:  # range sum query: 1 l r
            l = int(next(it))
            r = int(next(it))
            results.append(str(fenwick.range_sum(l, r)))
    
    sys.stdout.write("\n".join(results))

if __name__ == "__main__":
    main()