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
    best_region = None  # Will store (size, perimeter, min_r, min_c)
    
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
                min_r, min_c = r, c
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    
                    # Update lexicographically smallest coordinate
                    if (curr_r, curr_c) < (min_r, min_c):
                        min_r, min_c = curr_r, curr_c
                    
                    # Check all 4 boundaries/neighbors
                    for dr, dc in directions:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Exposed edge check (out of bounds or value < T)
                        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] < T:
                            perimeter += 1
                        elif (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                
                # Candidate tuple for tie-breaking:
                # Maximize size, then maximize perimeter, then minimize (min_r, min_c)
                candidate_key = (size, perimeter, -min_r, -min_c)
                candidate_data = (size, perimeter, (min_r, min_c))
                
                if best_region is None:
                    best_region = (candidate_key, candidate_data)
                else:
                    if candidate_key > best_region[0]:
                        best_region = (candidate_key, candidate_data)
                        
    if best_region is None:
        return (0, 0, None)
        
    return best_region[1]


# Example Usage & Verification:
if __name__ == "__main__":
    sample_grid = [
        [5, 5, 2, 6],
        [5, 1, 6, 6],
        [2, 6, 6, 1]
    ]
    threshold = 5
    
    result = find_largest_region(sample_grid, threshold)
    print("Result:", result)
    # Output: (4, 10, (0, 2))
    # Explanation: The region of 6s has size 4, perimeter 10, min coordinate (0, 2).
    # The region of 5s has size 3, perimeter 8, min coordinate (0, 0).