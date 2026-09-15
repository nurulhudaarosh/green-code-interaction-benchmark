from collections import deque

def find_largest_region(grid, T):
    """
    Finds the largest 4-connected region with cell values >= T.
    
    Returns:
        tuple: (size, perimeter, (min_row, min_col))
        If no cell >= T exists, returns (0, 0, None).
    """
    if not grid or not grid[0]:
        return (0, 0, None)
    
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    best_size = 0
    best_perimeter = 0
    best_min_coord = None
    
    # 4-directional offsets: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            if not visited[r][c] and grid[r][c] >= T:
                # Start iterative flood fill (BFS)
                visited[r][c] = True
                queue = deque([(r, c)])
                
                current_size = 0
                current_perimeter = 0
                current_min_coord = (r, c)
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    current_size += 1
                    current_min_coord = min(current_min_coord, (curr_r, curr_c))
                    
                    for dr, dc in directions:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Check boundary and value condition for perimeter counting
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr][nc] >= T:
                                if not visited[nr][nc]:
                                    visited[nr][nc] = True
                                    queue.append((nr, nc))
                            else:
                                # Neighbor value is below threshold
                                current_perimeter += 1
                        else:
                            # Neighbor is outside the grid boundary
                            current_perimeter += 1
                
                # Tie-breaking selection logic
                # Criteria: Max Size -> Max Perimeter -> Min Coordinate
                if (best_min_coord is None or
                    current_size > best_size or
                    (current_size == best_size and current_perimeter > best_perimeter) or
                    (current_size == best_size and current_perimeter == best_perimeter and current_min_coord < best_min_coord)):
                    
                    best_size = current_size
                    best_perimeter = current_perimeter
                    best_min_coord = current_min_coord
                    
    return (best_size, best_perimeter, best_min_coord)


# Example Usage
if __name__ == "__main__":
    sample_grid = [
        [1, 5, 5, 2],
        [0, 5, 3, 1],
        [4, 4, 4, 0],
        [4, 1, 4, 4]
    ]
    threshold = 4
    
    size, perimeter, min_coord = find_largest_region(sample_grid, threshold)
    print(f"Size: {size}, Perimeter: {perimeter}, Smallest Coord: {min_coord}")