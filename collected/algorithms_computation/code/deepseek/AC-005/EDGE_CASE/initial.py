def longest_increasing_subsequence_indices(a):
    n = len(a)
    if n == 0:
        return []
    
    dp = [1] * n
    prev = [-1] * n
    seq = [None] * n
    
    for i in range(n):
        seq[i] = (i,)
        for j in range(i):
            if a[j] < a[i]:
                cand_len = dp[j] + 1
                if cand_len > dp[i]:
                    dp[i] = cand_len
                    prev[i] = j
                    seq[i] = seq[j] + (i,)
                elif cand_len == dp[i]:
                    candidate = seq[j] + (i,)
                    if candidate < seq[i]:
                        prev[i] = j
                        seq[i] = candidate
    
    best_len = max(dp)
    candidates = [i for i in range(n) if dp[i] == best_len]
    best_seq = min(seq[i] for i in candidates)
    return list(best_seq)