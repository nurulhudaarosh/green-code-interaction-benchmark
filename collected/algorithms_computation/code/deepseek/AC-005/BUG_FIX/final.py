def longest_increasing_subsequence_indices(arr):
    n = len(arr)
    if n == 0:
        return []
    
    dp = [1] * n
    seq = [None] * n
    for i in range(n):
        seq[i] = (i,)
    
    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i]:
                if dp[j] + 1 > dp[i]:
                    dp[i] = dp[j] + 1
                    seq[i] = seq[j] + (i,)
                elif dp[j] + 1 == dp[i]:
                    candidate = seq[j] + (i,)
                    if candidate < seq[i]:
                        seq[i] = candidate
    
    max_len = max(dp)
    best_seq = None
    for i in range(n):
        if dp[i] == max_len:
            if best_seq is None or seq[i] < best_seq:
                best_seq = seq[i]
    
    return [idx + 1 for idx in best_seq]