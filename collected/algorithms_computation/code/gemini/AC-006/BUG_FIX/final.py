from collections import deque
from typing import List, Tuple, Optional

def find_largest_region(grid: List[List[int]], T: int) -> Tuple[int, int, Optional[Tuple[int, int]]]:
    """
    Finds the largest 4-connected region with cell values >= T.
    
    Returns:
        (size, perimeter, smallest_coordinate)
    """
    if not grid or not grid[0]:
        return (0, 0, None)
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    
    best_size = 0
    best_perimeter = 0
    best_min_coord = None
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] >= T and (r, c) not in visited:
                # Iterative flood fill for connected component
                queue = deque([(r, c)])
                visited.add((r, c))
                
                size = 0
                perimeter = 0
                min_coord = (r, c)
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    
                    # Update minimum coordinate in region
                    if (curr_r, curr_c) < min_coord:
                        min_coord = (curr_r, curr_c)
                    
                    # Check every exposed side for perimeter
                    for dr, dc in directions:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # An edge is exposed if it touches grid boundary or value < T
                        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] < T:
                            perimeter += 1
                        elif (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                
                # Deterministic tie handling:
                # 1. Maximize size
                # 2. Maximize perimeter
                # 3. Minimize starting/smallest coordinate tuple
                if best_min_coord is None:
                    best_size, best_perimeter, best_min_coord = size, perimeter, min_coord
                else:
                    cand_key = (size, perimeter, (-min_coord[0], -min_coord[1]))
                    best_key = (best_size, best_perimeter, (-best_min_coord[0], -best_min_coord[1]))
                    
                    if cand_key > best_key:
                        best_size, best_perimeter, best_min_coord = size, perimeter, min_coord
                        
    return (best_size, best_perimeter, best_min_coord)