def find_largest_region(grid, T):
    if not grid or not grid[0]:
        return (0, 0, (0, 0))
    
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    best_size = 0
    best_perimeter = 0
    best_coord = (float('inf'), float('inf'))
    
    # Directions: up, down, left, right
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            # Check if cell is valid and unvisited
            if grid[r][c] >= T and not visited[r][c]:
                # Start flood fill for this region
                stack = [(r, c)]
                visited[r][c] = True
                region_size = 0
                region_perimeter = 0
                min_row = r
                min_col = c
                
                while stack:
                    cr, cc = stack.pop()
                    region_size += 1
                    
                    # Update min coordinates
                    if cr < min_row or (cr == min_row and cc < min_col):
                        min_row = cr
                        min_col = cc
                    
                    # Check all 4 directions
                    for dr, dc in dirs:
                        nr, nc = cr + dr, cc + dc
                        
                        # Check if neighbor is within grid
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr][nc] >= T and not visited[nr][nc]:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                            elif grid[nr][nc] < T:
                                # Exposed side (neighbor has value < T)
                                region_perimeter += 1
                        else:
                            # Exposed side (outside grid)
                            region_perimeter += 1
                
                # Compare with best region
                if (region_size > best_size or
                    (region_size == best_size and region_perimeter > best_perimeter) or
                    (region_size == best_size and region_perimeter == best_perimeter and 
                     (min_row < best_coord[0] or 
                      (min_row == best_coord[0] and min_col < best_coord[1])))):
                    best_size = region_size
                    best_perimeter = region_perimeter
                    best_coord = (min_row, min_col)
    
    return (best_size, best_perimeter, best_coord)


# Example usage and test
if __name__ == "__main__":
    # Test case 1: Simple grid
    grid1 = [
        [5, 3, 1],
        [4, 6, 2],
        [7, 8, 9]
    ]
    T1 = 4
    result1 = find_largest_region(grid1, T1)
    print(f"Test 1: {result1}")
    # Expected: Region with values >= 4: cells (0,0)=5, (1,0)=4, (1,1)=6, (2,0)=7, (2,1)=8, (2,2)=9
    # Size=6, Perimeter=?, smallest coord=(0,0)
    
    # Test case 2: Multiple regions
    grid2 = [
        [5, 1, 5],
        [1, 5, 1],
        [5, 1, 5]
    ]
    T2 = 4
    result2 = find_largest_region(grid2, T2)
    print(f"Test 2: {result2}")
    # Expected: All 5s are isolated (size 1 each), but connected diagonally doesn't count
    # All have size 1, perimeter 4, smallest coord (0,0)
    
    # Test case 3: Region with perimeter
    grid3 = [
        [9, 9, 1],
        [9, 1, 9],
        [1, 9, 9]
    ]
    T3 = 8
    result3 = find_largest_region(grid3, T3)
    print(f"Test 3: {result3}")
    # Expected: Top-left 2x2 block of 9s (size 4), plus bottom-right 2x2 block of 9s (size 3)
    # Top-left has size 4, perimeter 8, coord (0,0)
    
    # Test case 4: Empty grid
    grid4 = []
    result4 = find_largest_region(grid4, T3)
    print(f"Test 4: {result4}")
    # Expected: (0, 0, (0, 0))
    
    # Test case 5: All cells below threshold
    grid5 = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    T5 = 10
    result5 = find_largest_region(grid5, T5)
    print(f"Test 5: {result5}")
    # Expected: (0, 0, (0, 0)) - no valid regions