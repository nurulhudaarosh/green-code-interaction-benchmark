from collections import deque

def find_largest_region(grid, T):
    """
    Finds the largest 4-connected region with cell values >= T.
    
    Returns:
        (size, perimeter, (min_row, min_col)) if a region exists,
        else (0, 0, None).
    """
    if not grid or not grid[0]:
        return (0, 0, None)
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    best_candidate = None
    
    # 4-directional vectors: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] >= T and (r, c) not in visited:
                # Start iterative flood fill (BFS)
                queue = deque([(r, c)])
                visited.add((r, c))
                
                size = 0
                perimeter = 0
                min_coord = (r, c)
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    
                    # Update minimum coordinate found in this region
                    if (curr_r, curr_c) < min_coord:
                        min_coord = (curr_r, curr_c)
                    
                    # Count exposed edges and discover unvisited region cells
                    for dr, dc in directions:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Edge exposed to boundary or cell < T
                        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] < T:
                            perimeter += 1
                        elif (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                
                candidate = (size, perimeter, min_coord)
                
                # Deterministic Tie-Handling:
                # 1. Larger size
                # 2. Larger perimeter
                # 3. Smaller coordinate (min_coord)
                if best_candidate is None:
                    best_candidate = candidate
                else:
                    b_size, b_perim, b_coord = best_candidate
                    c_size, c_perim, c_coord = candidate
                    
                    if (c_size > b_size) or \
                       (c_size == b_size and c_perim > b_perim) or \
                       (c_size == b_size and c_perim == b_perim and c_coord < b_coord):
                        best_candidate = candidate
                        
    if best_candidate is None:
        return (0, 0, None)
        
    return best_candidate