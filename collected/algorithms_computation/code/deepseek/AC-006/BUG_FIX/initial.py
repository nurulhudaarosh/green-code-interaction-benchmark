from collections import deque

def find_largest_region(grid, T):
    """
    Find the largest 4-connected region with values >= T.
    
    Args:
        grid: List of lists of integers
        T: Threshold integer
    
    Returns:
        Tuple (size, perimeter, (min_row, min_col))
    """
    if not grid or not grid[0]:
        return (0, 0, (0, 0))
    
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    # Directions: up, down, left, right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    best_size = 0
    best_perimeter = 0
    best_coord = (0, 0)
    
    for r in range(rows):
        for c in range(cols):
            # Start flood fill if cell is valid and unvisited
            if grid[r][c] >= T and not visited[r][c]:
                # Initialize region statistics
                region_size = 0
                region_perimeter = 0
                min_row = r
                min_col = c
                
                # BFS queue
                queue = deque()
                queue.append((r, c))
                visited[r][c] = True
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    region_size += 1
                    
                    # Update smallest coordinate
                    if curr_r < min_row or (curr_r == min_row and curr_c < min_col):
                        min_row = curr_r
                        min_col = curr_c
                    
                    # Check all 4 neighbors
                    for dr, dc in directions:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Check if neighbor is within grid bounds
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr][nc] >= T:
                                if not visited[nr][nc]:
                                    visited[nr][nc] = True
                                    queue.append((nr, nc))
                            else:
                                # Neighbor is outside region (value < T)
                                region_perimeter += 1
                        else:
                            # Edge of grid - exposed side
                            region_perimeter += 1
                
                # Compare with current best using tie-breaking rules
                if (region_size > best_size or
                    (region_size == best_size and region_perimeter > best_perimeter) or
                    (region_size == best_size and region_perimeter == best_perimeter and
                     (min_row < best_coord[0] or 
                      (min_row == best_coord[0] and min_col < best_coord[1])))):
                    best_size = region_size
                    best_perimeter = region_perimeter
                    best_coord = (min_row, min_col)
    
    return (best_size, best_perimeter, best_coord)


def solve():
    """
    Main function to read input and produce output.
    Input format:
    First line: rows cols T
    Next rows lines: grid values (space-separated integers)
    """
    import sys
    
    # Read all input
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    # Parse first line: rows, cols, T
    idx = 0
    rows = int(data[idx]); idx += 1
    cols = int(data[idx]); idx += 1
    T = int(data[idx]); idx += 1
    
    # Parse grid
    grid = []
    for _ in range(rows):
        row = []
        for _ in range(cols):
            row.append(int(data[idx]))
            idx += 1
        grid.append(row)
    
    # Find largest region
    size, perimeter, coord = find_largest_region(grid, T)
    
    # Output results
    print(f"{size} {perimeter} {coord[0]} {coord[1]}")


if __name__ == "__main__":
    solve()