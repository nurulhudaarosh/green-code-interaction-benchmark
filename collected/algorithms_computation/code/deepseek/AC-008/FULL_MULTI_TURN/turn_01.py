import sys

class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)  # 1-indexed

    def build(self, arr):
        # Build the tree in O(n) by adding each element
        for i, val in enumerate(arr, start=1):
            self.bit[i] += val
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]

    def update(self, idx, delta):
        # add delta at position idx (1-indexed)
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & -idx

    def prefix_sum(self, idx):
        # sum of [1..idx]
        s = 0
        while idx > 0:
            s += self.bit[idx]
            idx -= idx & -idx
        return s

    def range_sum(self, l, r):
        # sum of [l..r] inclusive (1-indexed)
        return self.prefix_sum(r) - self.prefix_sum(l - 1)

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    it = iter(data)
    n = int(next(it))
    arr = [int(next(it)) for _ in range(n)]
    
    ft = FenwickTree(n)
    ft.build(arr)
    
    q = int(next(it))
    out_lines = []
    for _ in range(q):
        typ = next(it).decode()
        if typ == 'update':
            idx = int(next(it))  # 1-indexed input
            new_val = int(next(it))
            # point replacement: add (new_val - old_value)
            old_val = arr[idx - 1]
            delta = new_val - old_val
            arr[idx - 1] = new_val
            ft.update(idx, delta)
        else:  # 'query'
            l = int(next(it))
            r = int(next(it))
            out_lines.append(str(ft.range_sum(l, r)))
    
    sys.stdout.write("\n".join(out_lines))

if __name__ == "__main__":
    main()