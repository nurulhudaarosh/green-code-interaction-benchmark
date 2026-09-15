import sys

def solve():
    # Read input: first integer n, then n integers
    data = sys.stdin.read().strip().split()
    if not data:
        return
    n = int(data[0])
    arr = list(map(int, data[1:1+n]))
    
    if n == 0:
        print()
        return
    
    dp = [1] * n
    best_seq = [(i,) for i in range(n)]
    
    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                cand_len = dp[j] + 1
                cand_seq = best_seq[j] + (i,)
                if cand_len > dp[i]:
                    dp[i] = cand_len
                    best_seq[i] = cand_seq
                elif cand_len == dp[i]:
                    if cand_seq < best_seq[i]:
                        best_seq[i] = cand_seq
    
    max_len = max(dp)
    # Find the lexicographically smallest among those with max_len
    best_overall = None
    for i in range(n):
        if dp[i] == max_len:
            if best_overall is None or best_seq[i] < best_overall:
                best_overall = best_seq[i]
    
    # Output indices (0-based) separated by space; if you want 1-based, add 1.
    # We'll output 0-based as per typical problem statement, but often they want 1-based.
    # Let's output 1-based to be safe (most problems use 1-based indices).
    print(' '.join(str(idx + 1) for idx in best_overall))

if __name__ == "__main__":
    solve()