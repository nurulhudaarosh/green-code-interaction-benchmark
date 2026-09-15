from collections import deque

def find_largest_region(grid, T):
    """
    Finds the largest 4-connected region with cell values >= T.
    
    Handles repeated grid values and deterministic ties strictly.
    
    Returns:
        dict: {'size': int, 'perimeter': int, 'smallest_coordinate': (r, c)}
        None: If no valid cell with value >= T exists.
    """
    if not grid or not grid[0]:
        return None

    rows, cols = len(grid), len(grid[0])
    visited = set()
    best_region_key = None
    best_region_data = None

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

                    # 4-connected orthogonal directions
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        # Check boundary and threshold conditions for perimeter
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr][nc] >= T:
                                if (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
                            else:
                                perimeter += 1
                        else:
                            perimeter += 1  # Out-of-bounds boundary edge

                # Deterministic tie-breaking key:
                # 1. Maximize size
                # 2. Maximize perimeter
                # 3. Minimize smallest coordinate (-r, -c)
                candidate_key = (size, perimeter, -min_coord[0], -min_coord[1])
                
                if best_region_key is None or candidate_key > best_region_key:
                    best_region_key = candidate_key
                    best_region_data = {
                        'size': size,
                        'perimeter': perimeter,
                        'smallest_coordinate': min_coord
                    }

    return best_region_data


# ==========================================
# Automated Test Suite
# ==========================================

def run_tests():
    # Test 1: Tie on size, resolved by larger perimeter
    # Region A at top-left: 2x2 square (size 4, perimeter 8)
    # Region B at bottom-right: 1x4 strip (size 4, perimeter 10)
    grid_1 = [
        [5, 5, 0, 0],
        [5, 5, 0, 0],
        [0, 0, 5, 5],
        [0, 0, 5, 5]  # Modified to form a connected strip vs square
    ]
    # Let's construct explicit shapes:
    grid_perimeter_tie = [
        [5, 5, 0, 0, 0],
        [5, 5, 0, 0, 0],  # Square A: size 4, perimeter 8, min_coord (0,0)
        [0, 0, 0, 0, 0],
        [5, 5, 5, 5, 0]   # Strip B:  size 4, perimeter 10, min_coord (3,0)
    ]
    res1 = find_largest_region(grid_perimeter_tie, 5)
    assert res1 == {'size': 4, 'perimeter': 10, 'smallest_coordinate': (3, 0)}, f"Failed Test 1: {res1}"

    # Test 2: Tie on size AND perimeter, resolved by smaller coordinate
    # Both regions are 1x2 strips (size 2, perimeter 6)
    # Region A min_coord: (0, 3)
    # Region B min_coord: (2, 0) -> (0, 3) < (2, 0) lexicographically
    grid_coord_tie = [
        [0, 0, 0, 5, 5],
        [0, 0, 0, 0, 0],
        [5, 5, 0, 0, 0]
    ]
    res2 = find_largest_region(grid_coord_tie, 5)
    assert res2 == {'size': 2, 'perimeter': 6, 'smallest_coordinate': (0, 3)}, f"Failed Test 2: {res2}"

    # Test 3: Repeated values & interior holes (donut shape)
    # Donut of 5s surrounding a 1
    grid_donut = [
        [5, 5, 5],
        [5, 1, 5],
        [5, 5, 5]
    ]
    # Size = 8, Outer perimeter = 12, Inner perimeter = 4, Total perimeter = 16
    res3 = find_largest_region(grid_donut, 5)
    assert res3 == {'size': 8, 'perimeter': 16, 'smallest_coordinate': (0, 0)}, f"Failed Test 3: {res3}"

    # Test 4: No cells >= Threshold
    grid_none = [[1, 2], [3, 4]]
    res4 = find_largest_region(grid_none, 10)
    assert res4 is None, f"Failed Test 4: {res4}"

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()