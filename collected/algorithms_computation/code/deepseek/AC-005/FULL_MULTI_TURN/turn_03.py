def solve(include_summary=False):
    import sys
    data = sys.stdin.read().strip().split()
    if not data:
        return
    n = int(data[0])
    a = list(map(int, data[1:1+n]))
    
    dp = [1] * n
    pred = [-1] * n
    seq = [None] * n
    
    # Statistics for summary
    total_pred_checks = 0
    total_comparisons = 0
    
    for i in range(n):
        best_len = 1
        best_pred = -1
        best_seq = (i,)
        for j in range(i):
            total_pred_checks += 1  # we check a[j] < a[i]
            if a[j] < a[i]:
                cand_len = dp[j] + 1
                cand_seq = seq[j] + (i,)
                total_comparisons += 1
                if cand_len > best_len:
                    best_len = cand_len
                    best_pred = j
                    best_seq = cand_seq
                elif cand_len == best_len:
                    total_comparisons += 1  # extra comparison for tie
                    if cand_seq < best_seq:
                        best_len = cand_len
                        best_pred = j
                        best_seq = cand_seq
        dp[i] = best_len
        pred[i] = best_pred
        seq[i] = best_seq
    
    # Find best end
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
    
    # Output
    result_indices = [idx + 1 for idx in best_seq]
    print(max_len)
    print(' '.join(map(str, result_indices)))
    
    if include_summary:
        summary = (f"Total predecessor checks: {total_pred_checks}, "
                   f"Total candidate comparisons: {total_comparisons}")
        print(summary, file=sys.stderr)  # or return as extra field

if __name__ == "__main__":
    # By default, don't include summary to preserve original output
    solve(include_summary=False)