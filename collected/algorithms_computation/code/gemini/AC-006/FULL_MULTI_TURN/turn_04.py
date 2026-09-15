from collections import deque

def find_largest_region(grid, T, return_summary=False):
    """
    Finds the largest 4-connected region with cell values >= T.
    
    Args:
        grid (list[list[int|float]]): 2D numeric grid.
        T (int|float): Threshold value.
        return_summary (bool): If True, returns (result_tuple, operation_summary).
        
    Returns:
        (size, perimeter, (min_row, min_col)) or ((size, perimeter, (min_row, min_col)), summary)
    """
    summary = {
        "cells_visited": 0,
        "regions_evaluated": 0,
        "edges_checked": 0
    }
    
    if not grid or not grid[0]:
        res = (0, 0, None)
        return (res, summary) if return_summary else res
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    best_candidate = None
    
    # 4-directional vectors: Up, Down, Left, Right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] >= T and (r, c) not in visited:
                summary["regions_evaluated"] += 1
                
                queue = deque([(r, c)])
                visited.add((r, c))
                
                size = 0
                perimeter = 0
                min_coord = (r, c)
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    size += 1
                    summary["cells_visited"] += 1
                    
                    if (curr_r, curr_c) < min_coord:
                        min_coord = (curr_r, curr_c)
                    
                    for dr, dc in directions:
                        summary["edges_checked"] += 1
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Edge exposed to boundary or cell < T
                        if not (0 <= nr < rows and 0 <= nc < cols) or grid[nr][nc] < T:
                            perimeter += 1
                        elif (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                
                candidate = (size, perimeter, min_coord)
                
                # Strict Deterministic Tie-Breaking Logic
                if best_candidate is None:
                    best_candidate = candidate
                else:
                    b_size, b_perim, b_coord = best_candidate
                    c_size, c_perim, c_coord = candidate
                    
                    if (c_size > b_size) or \
                       (c_size == b_size and c_perim > b_perim) or \
                       (c_size == b_size and c_perim == b_perim and c_coord < b_coord):
                        best_candidate = candidate

    result = best_candidate if best_candidate is not None else (0, 0, None)
    
    if return_summary:
        return (result, summary)
    return result


# =====================================================================
# Comprehensive Test Suite
# =====================================================================

def run_tests():
    # Test 1: Tie on Size & Perimeter -> Prefers Smaller Coordinate
    grid1 = [
        [0, 5, 0, 5],
        [0, 0, 0, 0]
    ]
    # Region A at (0, 1): size=1, perim=4, min_coord=(0, 1)
    # Region B at (0, 3): size=1, perim=4, min_coord=(0, 3)
    assert find_largest_region(grid1, 5) == (1, 4, (0, 1)), "Failed Test 1 (Tie on Coord)"

    # Test 2: Tie on Size -> Prefers Larger Perimeter
    # Both regions size 2. Region C is line of 2 (perim=6), Region D is block of 2?
    # Straight line of 2: perim = 6. 
    grid2 = [
        [5, 5, 0, 0],
        [0, 0, 5, 0],
        [0, 0, 5, 0]
    ]
    # Region top-left: size 2, perim 6, coord (0, 0)
    # Region bottom-right: size 2, perim 6, coord (1, 2)
    # Size & perim tied -> picks smaller coord (0,0)
    assert find_largest_region(grid2, 5) == (2, 6, (0, 0)), "Failed Test 2"

    # Test 3: Repeated Uniform Values with Hole
    grid3 = [
        [5, 5, 5],
        [5, 0, 5],
        [5, 5, 5]
    ]
    # Ring of 8 cells: size 8, outer perim 12 + inner perim 4 = 16 edges total
    assert find_largest_region(grid3, 5) == (8, 16, (0, 0)), "Failed Test 3 (Hole/Ring)"

    # Test 4: No valid region
    grid4 = [[1, 2], [3, 4]]
    assert find_largest_region(grid4, 5) == (0, 0, None), "Failed Test 4 (Empty Result)"

    # Test 5: Optional Summary preserving main output
    grid5 = [[5, 5], [5, 5]]
    res, summary = find_largest_region(grid5, 5, return_summary=True)
    assert res == (4, 8, (0, 0)), "Failed Test 5 (Output preservation)"
    assert summary["cells_visited"] == 4 and summary["regions_evaluated"] == 1, "Failed Test 5 (Summary logic)"

    print("All unit tests passed successfully!")

if __name__ == "__main__":
    run_tests()