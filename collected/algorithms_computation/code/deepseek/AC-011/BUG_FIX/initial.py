def knapsack_selection(weights, values, capacity):
    n = len(weights)
    W = capacity
    
    # suffix[i][w] = max value using items from i to n-1 with capacity w
    suffix = [[-10**9] * (W + 1) for _ in range(n + 1)]
    # base: suffix[n][w] = 0 for all w (no items left)
    for w in range(W + 1):
        suffix[n][w] = 0
    
    # fill suffix table from bottom to top
    for i in range(n - 1, -1, -1):
        wi, vi = weights[i], values[i]
        for w in range(W + 1):
            # skip item i
            best = suffix[i + 1][w]
            # take item i if possible
            if w >= wi:
                take = vi + suffix[i + 1][w - wi]
                if take > best:
                    best = take
            suffix[i][w] = best
    
    optimal_value = suffix[0][W]
    
    # reconstruct lexicographically smallest index list
    selected = []
    remaining_cap = W
    for i in range(n):
        wi, vi = weights[i], values[i]
        if wi <= remaining_cap:
            # check if taking item i leads to optimal value
            if vi + suffix[i + 1][remaining_cap - wi] == optimal_value:
                selected.append(i)
                remaining_cap -= wi
                optimal_value -= vi
        # else skip automatically
    return selected

# Example usage:
if __name__ == "__main__":
    weights = [2, 3, 4, 5]
    values  = [3, 4, 5, 6]
    cap = 8
    print(knapsack_selection(weights, values, cap))
    # Expected output: [0, 2] or [1, 2]? Both give value 8? Actually:
    # item0+item2 = 3+5=8, weight 2+4=6
    # item1+item2 = 4+5=9, weight 3+4=7 -> better
    # item0+item1 = 7, weight 5
    # item0+item3 = 9, weight 7 -> tie with item1+item2? values 9 both
    # Lexicographically smaller: [0, 3] vs [1, 2] => [0, 3] is smaller because first index 0 < 1
    # Our algorithm will produce [0, 3] if it leads to optimal value.