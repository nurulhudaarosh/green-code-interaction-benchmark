import sys

def longest_increasing_route_with_summary(seq):
    """
    Returns a dict with:
      - 'indices': 1‑based indices of the optimal subsequence
      - 'operation_summary': string with operation counts
    """
    n = len(seq)
    if n == 0:
        return {"indices": [], "operation_summary": "operations: 0, updates: 0"}

    dp = [1] * n
    best_seq = [(i,) for i in range(n)]

    total_pair_checks = 0
    total_updates = 0

    for i in range(n):
        for j in range(i):
            total_pair_checks += 1
            if seq[j] < seq[i]:
                cand_len = dp[j] + 1
                cand_seq = best_seq[j] + (i,)
                if cand_len > dp[i]:
                    dp[i] = cand_len
                    best_seq[i] = cand_seq
                    total_updates += 1
                elif cand_len == dp[i]:
                    if cand_seq < best_seq[i]:
                        best_seq[i] = cand_seq
                        total_updates += 1

    max_len = max(dp)
    best_overall = None
    for i in range(n):
        if dp[i] == max_len:
            if best_overall is None or best_seq[i] < best_overall:
                best_overall = best_seq[i]

    # Convert to 1‑based indices
    indices_1based = [idx + 1 for idx in best_overall]

    summary = f"operations: {total_pair_checks}, updates: {total_updates}"

    return {
        "indices": indices_1based,
        "operation_summary": summary
    }


def solve():
    data = sys.stdin.read().strip().split()
    if not data:
        return
    n = int(data[0])
    arr = list(map(int, data[1:1+n]))

    result = longest_increasing_route_with_summary(arr)

    # By default, output only the indices (original requirement)
    # But since we added the feature, we print both for demonstration.
    # In a real scenario, a flag would control this.
    print(" ".join(map(str, result["indices"])))
    # Optionally print the summary on a separate line (or as JSON)
    # Here we print it as a comment-like line for clarity
    print("#", result["operation_summary"])


if __name__ == "__main__":
    solve()