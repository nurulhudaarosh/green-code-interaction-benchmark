from collections import deque

def find_largest_region(grid, T):
    """
    Finds the largest 4-connected region with cell values >= T.
    
    Returns:
        dict containing 'size', 'perimeter', 'smallest_coordinate',
        or None if no valid cells exist.
    """
    if not grid or not grid[0]:
        return None

    rows, cols = len(grid), len(grid[0])
    visited = set()
    best_region = None  # Tuple: (size, perimeter, -min_r, -min_c, min_coord_tuple)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] >= T and (r, c) not in visited:
                # Iterative Flood Fill (BFS)
                queue = deque([(r, c)])
                visited.add((r, c))
                
                size = 0
                perimeter = 0
                min_coord = (r, c)

                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    
                    if (curr_r, curr_c) < min_coord:
                        min_coord = (curr_r, curr_c)

                    # Check 4 orthogonal directions
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Boundary or threshold check for perimeter
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr][nc] >= T:
                                if (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
                            else:
                                perimeter += 1
                        else:
                            perimeter += 1  # Out-of-bounds exposed edge

                # Tie-breaking key: (size, perimeter, -min_r, -min_c)
                candidate_key = (size, perimeter, -min_coord[0], -min_coord[1])
                
                if best_region is None or candidate_key > best_region[0]:
                    best_region = (candidate_key, {
                        'size': size,
                        'perimeter': perimeter,
                        'smallest_coordinate': min_coord
                    })

    return best_region[1] if best_region else None


# Example Usage:
if __name__ == "__main__":
    example_grid = [
        [1, 5, 5, 2],
        [5, 5, 1, 5],
        [5, 1, 5, 5]
    ]
    threshold = 5

    result = find_largest_region(example_grid, threshold)
    print("Result:", result)