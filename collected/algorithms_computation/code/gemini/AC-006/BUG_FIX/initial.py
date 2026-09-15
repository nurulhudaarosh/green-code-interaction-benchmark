from collections import deque
from typing import List, Tuple, Optional

def find_largest_region(grid: List[List[int]], T: int) -> Tuple[int, int, Optional[Tuple[int, int]]]:
    """
    Finds the largest 4-connected region with values >= T.
    
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
                # Start Flood Fill / BFS
                region_cells = []
                queue = deque([(r, c)])
                visited.add((r, c))
                
                min_coord = (r, c)
                perimeter = 0
                size = 0
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    min_coord = min(min_coord, (curr_r, curr_c))
                    
                    # Check 4 directions for perimeter and component traversal
                    for dr, dc in directions:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Boundary or less than threshold contributes to perimeter
                        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] < T:
                            perimeter += 1
                        else:
                            if (nr, nc) not in visited:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
                
                # Compare current region against the best region found so far
                current_candidate = (size, perimeter, min_coord)
                if best_min_coord is None:
                    best_size, best_perimeter, best_min_coord = current_candidate
                else:
                    # Compare: Larger size -> Larger perimeter -> Smaller coordinate
                    if (size > best_size) or \
                       (size == best_size and perimeter > best_perimeter) or \
                       (size == best_size and perimeter == best_perimeter and min_coord < best_min_coord):
                        best_size = size
                        best_perimeter = perimeter
                        best_min_coord = min_coord
                        
    return (best_size, best_perimeter, best_min_coord)


# Example Usage & Test Case
if __name__ == "__main__":
    grid_example = [
        [5, 5, 2, 1],
        [5, 1, 5, 5],
        [1, 1, 5, 5]
    ]
    threshold = 5
    
    result = find_largest_region(grid_example, threshold)
    print("Largest Region Result:", result)
    # Expected Output: (4, 8, (1, 2))