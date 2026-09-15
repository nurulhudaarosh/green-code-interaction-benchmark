def knapsack_selected_indices(weights, values, capacity):
    n = len(weights)
    # dp_val[w] = max value, dp_mask[w] = bitset of chosen indices
    NEG = -10**18
    dp_val = [NEG] * (capacity + 1)
    dp_mask = [0] * (capacity + 1)
    dp_val[0] = 0
    dp_mask[0] = 0

    for i in range(n):
        w = weights[i]
        v = values[i]
        # descending capacity
        for cap in range(capacity, w - 1, -1):
            if dp_val[cap - w] == NEG:
                continue
            new_val = dp_val[cap - w] + v
            new_mask = dp_mask[cap - w] | (1 << i)
            if new_val > dp_val[cap]:
                dp_val[cap] = new_val
                dp_mask[cap] = new_mask
            elif new_val == dp_val[cap]:
                # tie-break: choose lexicographically smaller index list
                # compare new_mask and dp_mask[cap]
                diff = new_mask ^ dp_mask[cap]
                if diff:
                    # lowest differing bit
                    low = diff & -diff
                    # if new_mask has 1 at low, it's lexicographically smaller
                    if new_mask & low:
                        dp_mask[cap] = new_mask
                    # else keep old
                # if diff==0, same mask, no change

    # find best (max value, then lexicographically smallest indices)
    best_val = NEG
    best_mask = 0
    for cap in range(capacity + 1):
        if dp_val[cap] > best_val:
            best_val = dp_val[cap]
            best_mask = dp_mask[cap]
        elif dp_val[cap] == best_val and dp_val[cap] != NEG:
            # tie-break between masks
            diff = dp_mask[cap] ^ best_mask
            if diff:
                low = diff & -diff
                # keep the one with 1 at lowest differing bit
                if dp_mask[cap] & low:
                    best_mask = dp_mask[cap]
    # extract indices
    indices = []
    for i in range(n):
        if best_mask & (1 << i):
            indices.append(i)
    return indices