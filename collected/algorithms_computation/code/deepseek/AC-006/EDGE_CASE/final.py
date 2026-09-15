import sys
from collections import deque

def find_best_region(grid, T):
    """Find the best 4-connected region with values >= T."""
    if not grid or not grid[0]:
        return 0, 0, (0, 0)
    
    R, C = len(grid), len(grid[0])
    visited = [[False] * C for _ in range(R)]
    
    best_size = 0
    best_perimeter = 0
    best_coord = (R, C)  # Initialize to max possible
    
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for start_r in range(R):
        for start_c in range(C):
            if visited[start_r][start_c] or grid[start_r][start_c] < T:
                continue
            
            # BFS flood fill
            queue = deque([(start_r, start_c)])
            visited[start_r][start_c] = True
            cells = []
            min_r, min_c = start_r, start_c
            
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                
                # Update smallest coordinate
                if r < min_r or (r == min_r and c < min_c):
                    min_r, min_c = r, c
                
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < R and 0 <= nc < C:
                        if not visited[nr][nc] and grid[nr][nc] >= T:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
            
            # Calculate perimeter: count exposed sides
            perimeter = 0
            for r, c in cells:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if nr < 0 or nr >= R or nc < 0 or nc >= C or grid[nr][nc] < T:
                        perimeter += 1
            
            size = len(cells)
            
            # Apply tie-breaking rules
            if (size > best_size or
                (size == best_size and perimeter > best_perimeter) or
                (size == best_size and perimeter == best_perimeter and 
                 (min_r < best_coord[0] or (min_r == best_coord[0] and min_c < best_coord[1])))):
                best_size = size
                best_perimeter = perimeter
                best_coord = (min_r, min_c)
    
    return best_size, best_perimeter, best_coord

def run_test_case(grid, T, expected_size, expected_perimeter, expected_coord, test_name):
    """Run a single test case and compare results."""
    size, perimeter, coord = find_best_region(grid, T)
    
    print(f"\n=== Test: {test_name} ===")
    print(f"Grid: {len(grid)}x{len(grid[0])}, T={T}")
    print("Grid:")
    for row in grid:
        print("  " + " ".join(str(x) for x in row))
    
    print(f"Result: size={size}, perimeter={perimeter}, coord={coord}")
    print(f"Expected: size={expected_size}, perimeter={expected_perimeter}, coord={expected_coord}")
    
    if (size == expected_size and perimeter == expected_perimeter and coord == expected_coord):
        print("✓ PASSED")
    else:
        print("✗ FAILED")
    
    return size == expected_size and perimeter == expected_perimeter and coord == expected_coord

def test_all():
    """Run all test cases."""
    passed = 0
    total = 0
    
    # Test 1: Basic case with multiple regions
    grid1 = [
        [5, 1, 5],
        [5, 5, 1],
        [1, 5, 5]
    ]
    # Region 1: top-left cluster (0,0),(1,0),(1,1) - size 3, perimeter 8
    # Region 2: top-right (0,2) - size 1, perimeter 4
    # Region 3: bottom-right (2,1),(2,2) - size 2, perimeter 6
    # Best: size 3, perimeter 8, coord (0,0)
    run_test_case(grid1, 5, 3, 8, (0, 0), "Basic multiple regions")
    total += 1
    
    # Test 2: Two regions with same size, different perimeter
    grid2 = [
        [5, 5, 0, 0],
        [5, 0, 0, 0],
        [0, 0, 5, 5],
        [0, 0, 5, 5]
    ]
    # Region A: 2x2 block at (0,0)-(1,1) but only cells >=5: (0,0),(0,1),(1,0) - size 3, perimeter 8
    # Region B: 2x2 block at (2,2)-(3,3) all 5s - size 4, perimeter 8
    # Best should be Region B: size 4, perimeter 8, coord (2,2)
    run_test_case(grid2, 5, 4, 8, (2, 2), "Same perimeter, different size")
    total += 1
    
    # Test 3: Same size, same perimeter, different coordinates
    grid3 = [
        [5, 0, 5],
        [0, 5, 0],
        [5, 0, 5]
    ]
    # Each isolated cell: size 1, perimeter 4
    # Smallest coordinate is (0,0)
    run_test_case(grid3, 5, 1, 4, (0, 0), "Same size/perimeter, different coords")
    total += 1
    
    # Test 4: Full grid all valid
    grid4 = [
        [5, 5, 5],
        [5, 5, 5],
        [5, 5, 5]
    ]
    # One region: size 9, perimeter 12
    run_test_case(grid4, 5, 9, 12, (0, 0), "Full grid region")
    total += 1
    
    # Test 5: Regions with holes (perimeter calculation)
    grid5 = [
        [5, 5, 5, 5],
        [5, 0, 0, 5],
        [5, 0, 0, 5],
        [5, 5, 5, 5]
    ]
    # One region with hole: size 12, perimeter 16 (outer 12 + inner 4)
    run_test_case(grid5, 5, 12, 16, (0, 0), "Region with hole")
    total += 1
    
    # Test 6: L-shaped region vs square region same size
    grid6 = [
        [5, 5, 5, 0],
        [5, 0, 0, 0],
        [5, 0, 5, 5],
        [0, 0, 5, 5]
    ]
    # Region A: L-shape at (0,0),(0,1),(0,2),(1,0),(2,0) - size 5, perimeter 12
    # Region B: 2x2 square at (2,2),(2,3),(3,2),(3,3) - size 4, perimeter 8
    # Best: size 5, perimeter 12, coord (0,0)
    run_test_case(grid6, 5, 5, 12, (0, 0), "L-shape vs square")
    total += 1
    
    # Test 7: Complex tie-breaking with same size, one has larger perimeter
    grid7 = [
        [5, 5, 0, 5],
        [5, 0, 0, 5],
        [5, 5, 5, 5],
        [0, 0, 0, 0]
    ]
    # Region A: shape at rows 0-2, cols 0-2 (minus center) - size 6, perimeter 12
    # Region B: shape at rows 0-2, col 3 - size 3, perimeter 8
    # Actually let's design two regions with same size:
    # Region 1: 2x3 rectangle at (0,0)-(1,2) - size 6, perimeter 10
    # Region 2: 3x2 rectangle at (0,2)-(2,3) - size 6, perimeter 10
    # Need different perimeters...
    
    # Simpler: two regions size 4, one is square (perimeter 8), one is line (perimeter 10)
    grid7b = [
        [5, 5, 0, 5],
        [5, 5, 0, 5],
        [0, 0, 0, 5],
        [0, 0, 0, 5]
    ]
    # Region A: 2x2 square at (0,0),(0,1),(1,0),(1,1) - size 4, perimeter 8, coord (0,0)
    # Region B: vertical line at col 3, rows 0-3 - size 4, perimeter 10, coord (0,3)
    # Best should be Region B (larger perimeter)
    run_test_case(grid7b, 5, 4, 10, (0, 3), "Same size, larger perimeter wins")
    total += 1
    
    # Test 8: No cells meet threshold
    grid8 = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ]
    run_test_case(grid8, 10, 0, 0, (3, 3), "No valid cells")
    total += 1
    
    print(f"\n{'='*50}")
    print(f"Tests passed: {passed}/{total}")
    return passed, total

def main():
    """Main function for production use."""
    # Read input
    line = sys.stdin.readline().strip()
    if not line:
        return
    
    R, C = map(int, line.split())
    grid = []
    for _ in range(R):
        row = list(map(int, sys.stdin.readline().split()))
        grid.append(row)
    
    T = int(sys.stdin.readline().strip())
    
    # Find and output the best region
    size, perimeter, coord = find_best_region(grid, T)
    print(size)
    print(perimeter)
    print(coord[0], coord[1])

if __name__ == "__main__":
    # Uncomment to run tests:
    # test_all()
    
    # Production mode:
    main()