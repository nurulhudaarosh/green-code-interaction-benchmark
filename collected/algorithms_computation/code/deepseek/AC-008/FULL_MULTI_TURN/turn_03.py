import sys
import json
import os

class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)
        self.step_count = 0  # track total loop iterations

    def build(self, arr):
        # O(n) build from array (1-indexed internally)
        for i, val in enumerate(arr, start=1):
            self.bit[i] += val
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]
            self.step_count += 1  # count build steps

    def update(self, idx, delta):
        # point update: add delta at position idx (1-indexed)
        steps = 0
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & -idx
            steps += 1
            self.step_count += 1
        return steps

    def prefix_sum(self, idx):
        # sum of [1..idx] inclusive
        s = 0
        steps = 0
        while idx > 0:
            s += self.bit[idx]
            idx -= idx & -idx
            steps += 1
            self.step_count += 1
        return s, steps

    def range_sum(self, l, r):
        # inclusive range sum [l..r]
        if l > r:
            return 0, 0
        sum_r, steps_r = self.prefix_sum(r)
        sum_l, steps_l = self.prefix_sum(l - 1)
        return sum_r - sum_l, steps_r + steps_l

def main():
    # Check if summary feature is enabled
    enable_summary = False
    if len(sys.argv) > 1 and sys.argv[1] == '--summary':
        enable_summary = True
    elif os.environ.get('ENABLE_SUMMARY') == '1':
        enable_summary = True
    
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
    
    # Summary counters
    total_operations = 0
    updates_performed = 0
    queries_performed = 0
    successful_updates = 0
    valid_queries = 0
    total_fenwick_steps = ft.step_count  # include build steps
    
    for _ in range(q):
        op = next(it).decode().lower()
        total_operations += 1
        
        if op == 'update':
            idx = int(next(it))
            new_val = int(next(it))
            updates_performed += 1
            if 1 <= idx <= n:
                old_val = arr[idx - 1]
                delta = new_val - old_val
                arr[idx - 1] = new_val
                steps = ft.update(idx, delta)
                total_fenwick_steps += steps
                successful_updates += 1
            # else: silently ignore for deterministic behavior
            
        elif op == 'query':
            l = int(next(it))
            r = int(next(it))
            queries_performed += 1
            # Validate and clamp to valid range for deterministic behavior
            orig_l, orig_r = l, r
            if l < 1: l = 1
            if r > n: r = n
            if l <= r:
                result, steps = ft.range_sum(l, r)
                total_fenwick_steps += steps
                out_lines.append(str(result))
                valid_queries += 1
            else:
                out_lines.append("0")  # deterministic handling
                # No Fenwick steps for invalid query
        else:
            # Unknown operation: deterministic skip (no-op)
            pass
    
    # Output query results (original behavior)
    output = "\n".join(out_lines)
    
    # Add summary if enabled
    if enable_summary:
        summary = {
            "total_operations": total_operations,
            "updates_performed": updates_performed,
            "queries_performed": queries_performed,
            "successful_updates": successful_updates,
            "valid_queries": valid_queries,
            "total_fenwick_steps": total_fenwick_steps
        }
        if output:
            output += "\n" + json.dumps(summary)
        else:
            output = json.dumps(summary)
    
    sys.stdout.write(output)

if __name__ == "__main__":
    main()