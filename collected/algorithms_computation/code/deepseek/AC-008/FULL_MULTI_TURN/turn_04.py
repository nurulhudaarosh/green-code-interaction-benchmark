import sys
import random
import time

class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)

    def build(self, arr):
        """O(n) build from array (1-indexed internally)"""
        for i, val in enumerate(arr, start=1):
            self.bit[i] += val
            j = i + (i & -i)
            if j <= self.n:
                self.bit[j] += self.bit[i]

    def update(self, idx, delta):
        """Point update: add delta at position idx (1-indexed)"""
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & -idx

    def prefix_sum(self, idx):
        """Sum of [1..idx] inclusive"""
        s = 0
        while idx > 0:
            s += self.bit[idx]
            idx -= idx & -idx
        return s

    def range_sum(self, l, r):
        """Inclusive range sum [l..r]"""
        if l > r:
            return 0
        return self.prefix_sum(r) - self.prefix_sum(l - 1)

def solve_mutable_range_sum(data):
    """Main solver function that processes input and returns outputs"""
    if not data:
        return []
    
    it = iter(data)
    n = int(next(it))
    arr = [int(next(it)) for _ in range(n)]
    
    ft = FenwickTree(n)
    ft.build(arr)
    
    q = int(next(it))
    outputs = []
    
    for _ in range(q):
        op = next(it).decode().lower()
        
        if op == 'update':
            idx = int(next(it))
            new_val = int(next(it))
            # Clamp index to valid range
            if 1 <= idx <= n:
                old_val = arr[idx - 1]
                delta = new_val - old_val
                if delta != 0:  # Skip no-op updates for efficiency
                    arr[idx - 1] = new_val
                    ft.update(idx, delta)
                else:
                    arr[idx - 1] = new_val  # Still update the stored array
            # else: ignore out-of-bounds updates
            
        elif op == 'query':
            l = int(next(it))
            r = int(next(it))
            # Clamp to valid range
            if l < 1: l = 1
            if r > n: r = n
            if l <= r:
                outputs.append(str(ft.range_sum(l, r)))
            else:
                outputs.append("0")
        else:
            # Unknown operation: skip
            pass
    
    return outputs

def run_tests():
    """Run comprehensive tests for worst-case and difficult cases"""
    print("Running tests for Mutable Range Sum Engine...")
    print("=" * 60)
    
    test_cases = []
    
    # Test 1: Basic functionality
    test_cases.append((
        "Basic operations",
        [5, 1, 2, 3, 4, 5, 4, 
         b'query', 1, 5,
         b'update', 3, 10,
         b'query', 2, 4,
         b'query', 1, 5],
        ["15", "19", "25"]
    ))
    
    # Test 2: Edge case - n=1
    test_cases.append((
        "Single element array",
        [1, 42, 3,
         b'query', 1, 1,
         b'update', 1, 100,
         b'query', 1, 1],
        ["42", "100"]
    ))
    
    # Test 3: Invalid indices (clamping)
    test_cases.append((
        "Invalid index clamping",
        [3, 10, 20, 30, 4,
         b'query', 0, 4,    # l clamped to 1
         b'query', 2, 5,    # r clamped to 3
         b'update', 0, 99,  # invalid update ignored
         b'query', 1, 3],
        ["60", "50", "60"]  # 10+20+30=60, 20+30=50, still 60
    ))
    
    # Test 4: l > r after clamping
    test_cases.append((
        "l > r case",
        [3, 5, 10, 15, 2,
         b'query', 3, 1,   # l > r, returns 0
         b'query', -1, -5], # both clamped to 1, l > r -> 0
        ["0", "0"]
    ))
    
    # Test 5: All updates (no queries)
    test_cases.append((
        "All updates, no queries",
        [3, 1, 2, 3, 2,
         b'update', 1, 10,
         b'update', 2, 20],
        []  # No output
    ))
    
    # Test 6: All queries (no updates)
    test_cases.append((
        "All queries, no updates",
        [3, 5, 6, 7, 3,
         b'query', 1, 3,
         b'query', 2, 2,
         b'query', 1, 1],
        ["18", "6", "5"]
    ))
    
    # Test 7: Large values (near 64-bit limit)
    test_cases.append((
        "Large 64-bit values",
        [2, 9223372036854775807, -9223372036854775808, 3,
         b'query', 1, 2,
         b'update', 1, 0,
         b'query', 1, 2],
        ["-1", "-9223372036854775808"]
    ))
    
    # Test 8: Alternating updates and queries (worst-case pattern)
    test_cases.append((
        "Alternating pattern (worst-case for Fenwick)",
        [4, 1, 2, 3, 4, 7,
         b'query', 1, 4,
         b'update', 1, 10,
         b'query', 1, 4,
         b'update', 2, 20,
         b'query', 1, 4,
         b'update', 3, 30,
         b'query', 1, 4],
        ["10", "19", "37", "67"]  # 1+2+3+4=10, 10+2+3+4=19, 10+20+3+4=37, 10+20+30+4=64
    ))
    
    # Test 9: Updates with delta=0 (no change)
    test_cases.append((
        "Zero-delta updates",
        [2, 5, 5, 4,
         b'query', 1, 2,
         b'update', 1, 5,  # no change
         b'query', 1, 2,
         b'update', 2, 5,  # no change
         b'query', 1, 2],
        ["10", "10", "10"]
    ))
    
    # Test 10: Large n and operations (synthetic worst-case)
    # We'll create a smaller version for testing but similar pattern
    test_cases.append((
        "Worst-case pattern: alternating extremes",
        [5, 1, 2, 3, 4, 5, 9,
         b'query', 1, 5,   # full range
         b'update', 1, 100,
         b'query', 5, 5,   # single element at end
         b'update', 5, 200,
         b'query', 1, 1,   # single element at start
         b'update', 3, 300,
         b'query', 2, 4,   # middle range
         b'update', 2, 400,
         b'query', 1, 5],  # full range again
        ["15", "205", "100", "703", "1103"]
        # Full: 1+2+3+4+5=15
        # After update 1->100: sum=100+2+3+4+5=114, query 5=5 (wait, need to recalc)
        # Let me recalc carefully:
        # Initial: [1,2,3,4,5] -> query 1-5 = 15
        # update 1->100: [100,2,3,4,5] -> query 5 = 5
        # update 5->200: [100,2,3,4,200] -> query 1 = 100
        # update 3->300: [100,2,300,4,200] -> query 2-4 = 2+300+4 = 306
        # query 1-5 = 100+2+300+4+200 = 606
        # So expected: ["15", "5", "100", "306", "606"]
    ))
    
    # Fix test 10 expected output
    test_cases[9] = (
        "Worst-case pattern: alternating extremes",
        [5, 1, 2, 3, 4, 5, 9,
         b'query', 1, 5,
         b'update', 1, 100,
         b'query', 5, 5,
         b'update', 5, 200,
         b'query', 1, 1,
         b'update', 3, 300,
         b'query', 2, 4,
         b'update', 2, 400,
         b'query', 1, 5],
        ["15", "5", "100", "306", "606"]
    )
    
    # Test 11: Random operations with brute force verification
    # We'll generate a small random test and verify against brute force
    random.seed(42)  # deterministic
    n_random = 50
    arr_random = [random.randint(-1000, 1000) for _ in range(n_random)]
    q_random = 100
    ops_random = [n_random] + arr_random + [q_random]
    brute = arr_random[:]
    
    # Generate random operations
    for _ in range(q_random):
        if random.random() < 0.4:  # 40% updates
            idx = random.randint(1, n_random)
            val = random.randint(-1000, 1000)
            ops_random.extend([b'update', idx, val])
        else:  # 60% queries
            l = random.randint(1, n_random)
            r = random.randint(1, n_random)
            if l > r:
                l, r = r, l
            ops_random.extend([b'query', l, r])
    
    # Compute expected with brute force
    expected_random = []
    ptr = 3  # skip n, arr, q
    current = brute[:]
    for _ in range(q_random):
        op = ops_random[ptr]
        ptr += 1
        if op == b'update':
            idx = ops_random[ptr]
            val = ops_random[ptr + 1]
            ptr += 2
            if 1 <= idx <= n_random:
                current[idx - 1] = val
        else:  # query
            l = ops_random[ptr]
            r = ops_random[ptr + 1]
            ptr += 2
            l = max(1, min(l, n_random))
            r = max(1, min(r, n_random))
            if l <= r:
                expected_random.append(str(sum(current[l-1:r])))
            else:
                expected_random.append("0")
    
    test_cases.append((
        "Random operations with brute force verification",
        ops_random,
        expected_random
    ))
    
    # Run all tests
    passed = 0
    failed = 0
    
    for name, input_data, expected in test_cases:
        try:
            # Convert input to bytes format expected by solver
            result = solve_mutable_range_sum(input_data)
            
            if result == expected:
                print(f"✓ PASS: {name}")
                passed += 1
            else:
                print(f"✗ FAIL: {name}")
                print(f"  Expected: {expected}")
                print(f"  Got:      {result}")
                failed += 1
        except Exception as e:
            print(f"✗ ERROR: {name}")
            print(f"  Exception: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    # Performance test for worst-case scale
    print("\n" + "=" * 60)
    print("Performance test on worst-case scale (n=100000, q=100000)")
    n_perf = 100000
    arr_perf = [i for i in range(n_perf)]
    q_perf = 100000
    
    # Build input data
    perf_data = [n_perf] + arr_perf + [q_perf]
    for i in range(q_perf):
        if i % 2 == 0:
            # Query full range (worst-case prefix sums)
            perf_data.extend([b'query', 1, n_perf])
        else:
            # Update middle index
            perf_data.extend([b'update', n_perf // 2, i])
    
    start_time = time.time()
    result_perf = solve_mutable_range_sum(perf_data)
    elapsed = time.time() - start_time
    
    print(f"Processed {q_perf} operations on {n_perf} elements")
    print(f"Time: {elapsed:.3f} seconds")
    print(f"Output count: {len(result_perf)}")
    print(f"Throughput: {q_perf / elapsed:.0f} ops/sec")
    print("✓ Performance test completed (no correctness verification for scale)")
    
    return passed, failed

def main():
    """Main entry point for actual problem solving"""
    data = sys.stdin.buffer.read().split()
    if not data:
        return
    
    outputs = solve_mutable_range_sum(data)
    sys.stdout.write("\n".join(outputs))

if __name__ == "__main__":
    # Check if we're running tests
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_tests()
    else:
        main()