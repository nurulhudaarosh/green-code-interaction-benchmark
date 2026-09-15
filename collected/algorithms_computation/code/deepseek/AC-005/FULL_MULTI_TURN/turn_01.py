def solve():
    import sys
    data = sys.stdin.read().strip().split()
    if not data:
        return
    n = int(data[0])
    a = list(map(int, data[1:1+n]))
    
    # dp[i] = length of LIS ending at i
    dp = [1] * n
    # pred[i] = previous index in the optimal subsequence, -1 if none
    pred = [-1] * n
    # We'll store the index sequence for each i to compare lexicographically
    # To save memory, we can store the sequence as tuple of indices (0-based)
    seq = [None] * n
    for i in range(n):
        seq[i] = (i,)
    
    for i in range(n):
        best_len = 1
        best_pred = -1
        best_seq = (i,)
        for j in range(i):
            if a[j] < a[i]:
                # candidate length
                cand_len = dp[j] + 1
                # candidate sequence
                cand_seq = seq[j] + (i,)
                if cand_len > best_len:
                    best_len = cand_len
                    best_pred = j
                    best_seq = cand_seq
                elif cand_len == best_len:
                    # lexicographically smaller sequence?
                    if cand_seq < best_seq:
                        best_len = cand_len
                        best_pred = j
                        best_seq = cand_seq
        dp[i] = best_len
        pred[i] = best_pred
        seq[i] = best_seq
    
    # Find the best end: max length, tie break by lexicographically smallest sequence
    max_len = -1
    best_end = -1
    best_seq = None
    for i in range(n):
        if dp[i] > max_len:
            max_len = dp[i]
            best_end = i
            best_seq = seq[i]
        elif dp[i] == max_len:
            if seq[i] < best_seq:
                best_end = i
                best_seq = seq[i]
    
    # Reconstruct indices (convert to 1-based for output)
    result_indices = [idx + 1 for idx in best_seq]
    
    # Output: first line length, second line indices separated by space
    print(max_len)
    print(' '.join(map(str, result_indices)))

if __name__ == "__main__":
    solve()