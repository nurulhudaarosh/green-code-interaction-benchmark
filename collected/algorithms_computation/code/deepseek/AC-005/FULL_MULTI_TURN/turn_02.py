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