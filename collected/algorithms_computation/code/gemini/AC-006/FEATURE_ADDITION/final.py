from collections import deque

def find_largest_region(grid, threshold, include_summary=False):
    """
    Finds the largest 4-connected region with values >= threshold.
    
    Args:
        grid (list[list[int/float]]): 2D numeric array.
        threshold (int/float): Threshold value T.
        include_summary (bool): If True, appends operation_summary to output.
        
    Returns:
        tuple: (size, perimeter, smallest_coordinate)
        OR if include_summary=True:
        tuple: (size, perimeter, smallest_coordinate, operation_summary)
    """
    summary = {
        "total_cells_checked": 0,
        "valid_cells_processed": 0,
        "regions_evaluated": 0,
        "neighbor_edges_inspected": 0
    }

    if not grid or not grid[0]:
        if include_summary:
            return (0, 0, None, summary)
        return (0, 0, None)
    
    rows, cols = len(grid), len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    best_size = 0
    best_perimeter = 0
    best_min_coord = None
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            summary["total_cells_checked"] += 1
            
            if not visited[r][c] and grid[r][c] >= threshold:
                summary["regions_evaluated"] += 1
                
                # Start iterative flood fill (BFS)
                queue = deque([(r, c)])
                visited[r][c] = True
                
                size = 0
                perimeter = 0
                min_coord = (r, c)
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    summary["valid_cells_processed"] += 1
                    
                    if (curr_r, curr_c) < min_coord:
                        min_coord = (curr_r, curr_c)
                    
                    for dr, dc in directions:
                        summary["neighbor_edges_inspected"] += 1
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        if not (0 <= nr < rows and 0 <= nc < cols):
                            perimeter += 1
                        elif grid[nr][nc] < threshold:
                            perimeter += 1
                        else:
                            if not visited[nr][nc]:
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                
                # Compare against current best component
                if best_min_coord is None:
                    best_size, best_perimeter, best_min_coord = size, perimeter, min_coord
                else:
                    current_key = (size, perimeter, -min_coord[0], -min_coord[1])
                    best_key = (best_size, best_perimeter, -best_min_coord[0], -best_min_coord[1])
                    
                    if current_key > best_key:
                        best_size, best_perimeter, best_min_coord = size, perimeter, min_coord

    result = (best_size, best_perimeter, best_min_coord)
    
    if include_summary:
        return result + (summary,)
    return result


# --- Verification Example ---
if __name__ == "__main__":
    grid = [
        [5, 5, 2, 4],
        [5, 1, 4, 4],
        [2, 4, 4, 1]
    ]
    T = 4

    print("Default Call:", find_largest_region(grid, T))
    
    size, perimeter, coord, ops = find_largest_region(grid, T, include_summary=True)
    print("\nWith Summary:")
    print(f"Size: {size}, Perimeter: {perimeter}, Min Coord: {coord}")
    print("Operations Summary:", ops)