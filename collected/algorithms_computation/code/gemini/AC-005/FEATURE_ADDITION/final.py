from typing import List, Dict, Any, Union

def longest_increasing_route(
    arr: List[int], 
    include_summary: bool = False
) -> Union[List[int], Dict[str, Any]]:
    """
    Finds the strictly increasing subsequence of maximum length with the 
    lexicographically smallest 0-based index path.
    
    :param arr: Input sequence of integers.
    :param include_summary: If True, returns a dict with 'route' and 'operation_summary'.
                            If False, returns only the list of indices.
    :return: List of 0-based indices or a Dictionary containing the route and summary.
    """
    n = len(arr)
    
    # Operation counters
    transitions_evaluated = 0
    valid_expansions = 0
    path_updates = 0

    if n == 0:
        route = []
        if include_summary:
            return {
                "route": route,
                "operation_summary": {
                    "elements_processed": 0,
                    "transitions_evaluated": 0,
                    "valid_expansions": 0,
                    "path_updates": 0
                }
            }
        return route

    # dp[i] stores the length of LIS ending at i
    dp = [1] * n
    # path[i] stores the complete 0-based index sequence ending at i
    path = [[i] for i in range(n)]

    for i in range(n):
        for j in range(i):
            transitions_evaluated += 1
            if arr[j] < arr[i]:
                valid_expansions += 1
                candidate_len = dp[j] + 1
                candidate_path = path[j] + [i]
                
                # Check for strictly longer path OR lexicographically smaller index path
                if candidate_len > dp[i]:
                    dp[i] = candidate_len
                    path[i] = candidate_path
                    path_updates += 1
                elif candidate_len == dp[i] and candidate_path < path[i]:
                    path[i] = candidate_path
                    path_updates += 1

    # Identify global maximum length
    max_len = max(dp)
    
    # Select the lexicographically smallest path among all achieving max_len
    best_path = None
    for i in range(n):
        if dp[i] == max_len:
            if best_path is None or path[i] < best_path:
                best_path = path[i]

    route = best_path if best_path is not None else []

    if include_summary:
        return {
            "route": route,
            "operation_summary": {
                "elements_processed": n,
                "transitions_evaluated": transitions_evaluated,
                "valid_expansions": valid_expansions,
                "path_updates": path_updates
            }
        }
    
    return route


# Example Usage
if __name__ == "__main__":
    nums = [10, 22, 9, 33, 21, 50, 41, 60, 80]
    
    # 1. Backward Compatible Call (default)
    default_res = longest_increasing_route(nums)
    print("Default Output (Route Only):", default_res)
    
    # 2. Call with Summary Enabled
    summary_res = longest_increasing_route(nums, include_summary=True)
    print("\nOutput with Operation Summary:")
    print("Route:", summary_res["route"])
    print("Summary:", summary_res["operation_summary"])