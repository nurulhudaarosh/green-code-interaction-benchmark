from collections import deque

def find_largest_region(grid, threshold):
    """
    Finds the largest 4-connected region with values >= threshold.
    
    Returns:
        tuple: (size, perimeter, smallest_coordinate)
               Returns (0, 0, None) if no valid cells exist.
    """
    if not grid or not grid[0]:
        return (0, 0, None)
    
    rows, cols = len(grid), len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    best_size = 0
    best_perimeter = 0
    best_min_coord = None
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            if not visited[r][c] and grid[r][c] >= threshold:
                # Start iterative flood fill (BFS)
                queue = deque([(r, c)])
                visited[r][c] = True
                
                size = 0
                perimeter = 0
                min_coord = (r, c)
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    
                    # Track smallest coordinate lexicographically
                    if (curr_r, curr_c) < min_coord:
                        min_coord = (curr_r, curr_c)
                    
                    # Count exposed perimeter sides and queue valid adjacent cells
                    for dr, dc in directions:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Out of bounds boundary adds to perimeter
                        if not (0 <= nr < rows and 0 <= nc < cols):
                            perimeter += 1
                        # Cell value below threshold adds to perimeter
                        elif grid[nr][nc] < threshold:
                            perimeter += 1
                        # Valid neighbor cell within component
                        else:
                            if not visited[nr][nc]:
                                visited[nr][nc] = True
                                queue.append((nr, nc))
                
                # Compare against best candidate
                # Tie-breaking priority: Max size -> Max perimeter -> Min coordinate
                if best_min_coord is None:
                    best_size, best_perimeter, best_min_coord = size, perimeter, min_coord
                else:
                    current_key = (size, perimeter, -min_coord[0], -min_coord[1])
                    best_key = (best_size, best_perimeter, -best_min_coord[0], -best_min_coord[1])
                    
                    if current_key > best_key:
                        best_size, best_perimeter, best_min_coord = size, perimeter, min_coord

    return (best_size, best_perimeter, best_min_coord)


# --- Verification Example ---
if __name__ == "__main__":
    grid = [
        [5, 5, 2, 4],
        [5, 1, 4, 4],
        [2, 4, 4, 1]
    ]
    T = 4
    
    size, perimeter, min_coord = find_largest_region(grid, T)
    print(f"Size: {size}")
    print(f"Perimeter: {perimeter}")
    print(f"Smallest Coordinate: {min_coord}")