from typing import Dict, List, Tuple, Union, Any

def knapsack_01(
    weights: List[int], 
    values: List[int], 
    capacity: int, 
    include_summary: bool = False
) -> Union[List[int], Dict[str, Any]]:
    """
    Solves the 0/1 Knapsack problem with lexicographical tie-breaking.
    
    Args:
        weights: List of item weights.
        values: List of item values.
        capacity: Maximum knapsack weight capacity.
        include_summary: If True, returns a dict with 'selected_indices' and 'operation_summary'.
                         If False, returns only 'selected_indices'.
                         
    Returns:
        List of selected original 0-based indices, or a dictionary containing the results 
        and execution metrics if include_summary=True.
    """
    n = len(weights)
    
    # dp[w] stores a tuple: (max_value, list_of_selected_indices)
    dp: List[Tuple[int, List[int]]] = [(0, []) for _ in range(capacity + 1)]
    
    total_evaluations = 0
    state_updates = 0
    
    for i in range(n):
        w_i = weights[i]
        v_i = values[i]
        
        # Descending capacity update to ensure 0/1 item usage
        for w in range(capacity, w_i - 1, -1):
            total_evaluations += 1
            
            prev_val, prev_indices = dp[w - w_i]
            candidate_val = prev_val + v_i
            candidate_indices = prev_indices + [i]
            
            current_val, current_indices = dp[w]
            
            # Decision logic: strict value improvement or lexicographical tie-break
            should_update = False
            if candidate_val > current_val:
                should_update = True
            elif candidate_val == current_val and candidate_val > 0:
                if candidate_indices < current_indices:
                    should_update = True
                    
            if should_update:
                dp[w] = (candidate_val, candidate_indices)
                state_updates += 1
                
    # Determine maximum value achieved
    max_value = max(val for val, _ in dp)
    
    # Select the lexicographically smallest index list among states achieving max_value
    best_indices: Union[List[int], None] = None
    for val, indices in dp:
        if val == max_value:
            if best_indices is None or indices < best_indices:
                best_indices = indices
                
    result_indices = best_indices if best_indices is not None else []
    
    if not include_summary:
        return result_indices
        
    return {
        "selected_indices": result_indices,
        "operation_summary": {
            "total_state_evaluations": total_evaluations,
            "state_updates": state_updates,
            "max_value_found": max_value
        }
    }


# Example Usage
if __name__ == "__main__":
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    capacity = 5
    
    # Original behavior (backward-compatible)
    indices_only = knapsack_01(weights, values, capacity)
    print("Original Output Format:", indices_only)
    
    # Detailed summary behavior
    detailed_result = knapsack_01(weights, values, capacity, include_summary=True)
    print("Extended Output Format:", detailed_result)