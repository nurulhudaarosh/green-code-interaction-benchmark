from typing import List, Tuple

def min_coin_change(coins: List[int], amount: int) -> Tuple[int, List[int]]:
    if amount == 0:
        return 0, []
    if amount < 0 or not coins:
        return -1, []

    # Sort and remove duplicates from coin denominations
    unique_coins = sorted(list(set(coins)))

    # dp[i] will store a tuple: (coin_count, canonical_combination_list)
    # Target value initialized to infinity
    inf = float('inf')
    dp = [(inf, []) for _ in range(amount + 1)]
    dp[0] = (0, [])

    for i in range(1, amount + 1):
        best_count = inf
        best_comb = None

        for coin in unique_coins:
            if i - coin >= 0:
                prev_count, prev_comb = dp[i - coin]
                if prev_count != inf:
                    candidate_count = prev_count + 1
                    # Candidate path sorted deterministically
                    candidate_comb = sorted(prev_comb + [coin])

                    if candidate_count < best_count:
                        best_count = candidate_count
                        best_comb = candidate_comb
                    elif candidate_count == best_count:
                        # Tie-breaking: Choose lexicographically smaller sorted combination
                        if best_comb is None or candidate_comb < best_comb:
                            best_comb = candidate_comb

        if best_comb is not None:
            dp[i] = (best_count, best_comb)

    count, combination = dp[amount]
    if count == inf:
        return -1, []

    return count, combination


if __name__ == "__main__":
    # Test demonstrating fix for tie-handling
    coins = [2, 3, 5, 6]
    target = 8
    count, combination = min_coin_change(coins, target)
    print(f"Target: {target}")
    print(f"Minimum Coins: {count}")
    print(f"Coins Used (Canonical Lexicographical Tie-Breaker): {combination}")