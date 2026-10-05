import sys

def solve(stages, budget_limit, memory_limit):
    """
    stages: list of lists of (cost, memory, score) tuples
    Returns: list of chosen option indices (lexicographically smallest among optimal)
    """
    n = len(stages)
    
    # dp[b][m] = best score using processed stages so far
    NEG = float('-inf')
    dp = [[NEG] * (memory_limit + 1) for _ in range(budget_limit + 1)]
    dp[0][0] = 0
    
    # parent[i][b][m] = (prev_b, prev_m, option_index) for reconstruction
    # We store per-stage snapshots
    parents = []
    
    for i in range(n):
        new_dp = [[NEG] * (memory_limit + 1) for _ in range(budget_limit + 1)]
        parent = [[None] * (memory_limit + 1) for _ in range(budget_limit + 1)]
        
        options = stages[i]
        for b in range(budget_limit + 1):
            row = dp[b]
            for m in range(memory_limit + 1):
                cur = row[m]
                if cur == NEG:
                    continue
                for j, (c, mem, s) in enumerate(options):
                    nb = b + c
                    nm = m + mem
                    if nb <= budget_limit and nm <= memory_limit:
                        val = cur + s
                        if val > new_dp[nb][nm]:
                            new_dp[nb][nm] = val
                            parent[nb][nm] = (b, m, j)
                        # Tie-break during forward pass: prefer smaller option index
                        elif val == new_dp[nb][nm]:
                            prev = parent[nb][nm]
                            if prev is not None and j < prev[2]:
                                parent[nb][nm] = (b, m, j)
        
        parents.append(parent)
        dp = new_dp
    
    # Find best final state
    best_score = NEG
    best_b = best_m = -1
    for b in range(budget_limit + 1):
        for m in range(memory_limit + 1):
            if dp[b][m] > best_score:
                best_score = dp[b][m]
                best_b, best_m = b, m
    
    if best_score == NEG:
        return None  # No feasible solution
    
    # Reconstruct
    choices = [0] * n
    b, m = best_b, best_m
    for i in range(n - 1, -1, -1):
        pb, pm, j = parents[i][b][m]
        choices[i] = j
        b, m = pb, pm
    
    return choices


def main():
    data = sys.stdin.read().split()
    if not data:
        return
    idx = 0
    n = int(data[idx]); idx += 1
    budget_limit = int(data[idx]); idx += 1
    memory_limit = int(data[idx]); idx += 1
    
    stages = []
    for _ in range(n):
        k = int(data[idx]); idx += 1
        opts = []
        for _ in range(k):
            c = int(data[idx]); idx += 1
            mem = int(data[idx]); idx += 1
            s = int(data[idx]); idx += 1
            opts.append((c, mem, s))
        stages.append(opts)
    
    result = solve(stages, budget_limit, memory_limit)
    if result is None:
        print("NO SOLUTION")
    else:
        print(' '.join(map(str, result)))


if __name__ == "__main__":
    main()