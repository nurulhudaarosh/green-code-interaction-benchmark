from collections import deque

def find_largest_region(grid, T):
    """
    Find the largest 4-connected region with values >= T.
    
    Returns:
        Tuple (size, perimeter, (min_row, min_col))
    """
    if not grid or not grid[0]:
        return (0, 0, (0, 0))
    
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    # 4-directional moves: up, down, left, right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    best_size = 0
    best_perimeter = 0
    best_coord = (0, 0)
    
    for start_r in range(rows):
        for start_c in range(cols):
            # Skip if invalid or already visited
            if grid[start_r][start_c] < T or visited[start_r][start_c]:
                continue
            
            # Start BFS for a new region
            queue = deque([(start_r, start_c)])
            visited[start_r][start_c] = True
            
            region_cells = []  # Store cells for perimeter calculation
            region_size = 0
            min_row, min_col = start_r, start_c
            
            # BFS to find all cells in region
            while queue:
                r, c = queue.popleft()
                region_cells.append((r, c))
                region_size += 1
                
                # Update minimum coordinate
                if r < min_row or (r == min_row and c < min_col):
                    min_row, min_col = r, c
                
                # Explore neighbors
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if grid[nr][nc] >= T and not visited[nr][nc]:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
            
            # Calculate perimeter for this region
            perimeter = 0
            for r, c in region_cells:
                # Check all 4 sides of this cell
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    
                    # If neighbor is outside grid or has value < T, this side is exposed
                    if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] < T:
                        perimeter += 1
            
            # Compare with best using tie-breaking rules
            if (region_size > best_size or
                (region_size == best_size and perimeter > best_perimeter) or
                (region_size == best_size and perimeter == best_perimeter and
                 (min_row < best_coord[0] or 
                  (min_row == best_coord[0] and min_col < best_coord[1])))):
                best_size = region_size
                best_perimeter = perimeter
                best_coord = (min_row, min_col)
    
    return best_size, best_perimeter, best_coord


def solve():
    import sys
    
    data = sys.stdin.read().strip().split()
    if not data:
        return
    
    idx = 0
    rows = int(data[idx]); idx += 1
    cols = int(data[idx]); idx += 1
    T = int(data[idx]); idx += 1
    
    grid = []
    for _ in range(rows):
        row = []
        for _ in range(cols):
            row.append(int(data[idx]))
            idx += 1
        grid.append(row)
    
    size, perimeter, coord = find_largest_region(grid, T)
    print(f"{size} {perimeter} {coord[0]} {coord[1]}")


if __name__ == "__main__":
    solve()