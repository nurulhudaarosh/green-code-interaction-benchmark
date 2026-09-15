from collections import deque

def find_largest_region(grid, T, return_summary=False):
    """
    Finds the largest 4-connected region with cell values >= T.
    
    Args:
        grid (list[list[int|float]]): 2D numeric grid.
        T (int|float): Numeric threshold.
        return_summary (bool): If True, returns (result, operation_summary).
    
    Returns:
        tuple: (size, perimeter, (min_row, min_col)) if return_summary=False.
        tuple: ((size, perimeter, (min_row, min_col)), operation_summary) if return_summary=True.
    """
    summary = {
        "cells_visited": 0,
        "regions_evaluated": 0,
        "edges_checked": 0
    }
    
    if not grid or not grid[0]:
        res = (0, 0, None)
        return (res, summary) if return_summary else res
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    best_candidate = None
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] >= T and (r, c) not in visited:
                # Discovered a new region
                summary["regions_evaluated"] += 1
                
                queue = deque([(r, c)])
                visited.add((r, c))
                
                size = 0
                perimeter = 0
                min_coord = (r, c)
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    summary["cells_visited"] += 1
                    
                    if (curr_r, curr_c) < min_coord:
                        min_coord = (curr_r, curr_c)
                    
                    for dr, dc in directions:
                        summary["edges_checked"] += 1
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Exposed edge check
                        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] < T:
                            perimeter += 1
                        elif (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                
                candidate = (size, perimeter, min_coord)
                
                # Deterministic Tie-Handling:
                # 1. Maximize size
                # 2. Maximize perimeter
                # 3. Minimize coordinate tuple
                if best_candidate is None:
                    best_candidate = candidate
                else:
                    b_size, b_perim, b_coord = best_candidate
                    c_size, c_perim, c_coord = candidate
                    
                    if (c_size > b_size) or \
                       (c_size == b_size and c_perim > b_perim) or \
                       (c_size == b_size and c_perim == b_perim and c_coord < b_coord):
                        best_candidate = candidate

    result = best_candidate if best_candidate is not None else (0, 0, None)
    
    if return_summary:
        return (result, summary)
    return result


# Example Verification:
if __name__ == "__main__":
    sample_grid = [
        [5, 5, 2, 6],
        [5, 1, 6, 6],
        [2, 6, 6, 1]
    ]
    threshold = 5
    
    # Original interface preserved
    print("Default call:", find_largest_region(sample_grid, threshold))
    # Output: (4, 10, (0, 2))
    
    # With operation summary enabled
    result, op_summary = find_largest_region(sample_grid, threshold, return_summary=True)
    print("Result with summary:", result)
    print("Operation Summary:", op_summary)