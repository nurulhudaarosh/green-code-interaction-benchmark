"""
Problem: Given a numeric grid and threshold T, find the largest 4-connected region
of cells with value >= T. Return its size, perimeter, and smallest coordinate.
Ties: prefer larger perimeter, then smaller coordinate (row-major order).

Algorithm: Iterative flood fill (DFS using stack), count every exposed side.
"""

from typing import List, Tuple, Any

def find_largest_region(grid: List[List[Any]], T: Any) -> Tuple[int, int, Tuple[int, int]]:
    if not grid or not grid[0]:
        return (0, 0, (0, 0))
    
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    best_size = 0
    best_perim = 0
    best_coord = None  # Will be set when first region is found
    
    # Directions: up, down, left, right
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            if visited[r][c] or grid[r][c] < T:
                continue
            
            # Start flood fill
            stack = [(r, c)]
            visited[r][c] = True
            size = 0
            perim = 0
            min_r, min_c = r, c
            
            while stack:
                cr, cc = stack.pop()
                size += 1
                
                # Update smallest coordinate (row-major)
                if cr < min_r or (cr == min_r and cc < min_c):
                    min_r, min_c = cr, cc
                
                # Check 4 neighbors
                for dr, dc in dirs:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if grid[nr][nc] >= T:
                            if not visited[nr][nc]:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                            # If neighbor is in region, it's NOT an exposed side
                            # (we already visited it or it's in stack)
                            # No perimeter added for internal edges
                        else:
                            # Neighbor exists but value < T -> boundary
                            perim += 1
                    else:
                        # Out of bounds -> boundary
                        perim += 1
            
            # Compare with best
            if best_coord is None:
                # First region found
                best_size = size
                best_perim = perim
                best_coord = (min_r, min_c)
            else:
                # Compare: larger size wins
                if size > best_size:
                    best_size = size
                    best_perim = perim
                    best_coord = (min_r, min_c)
                elif size == best_size:
                    # Tie on size: larger perimeter wins
                    if perim > best_perim:
                        best_perim = perim
                        best_coord = (min_r, min_c)
                    elif perim == best_perim:
                        # Tie on perimeter: smaller coordinate wins
                        if min_r < best_coord[0] or (min_r == best_coord[0] and min_c < best_coord[1]):
                            best_coord = (min_r, min_c)
                            # best_size and best_perim remain the same
    
    # If no region found, return zeros
    if best_coord is None:
        return (0, 0, (0, 0))
    
    return (best_size, best_perim, best_coord)


# Test the correction
if __name__ == "__main__":
    # Test case 1: Two regions same size, different perimeter
    grid1 = [
        [4, 4, 1],
        [4, 1, 1],
        [1, 1, 1]
    ]
    T = 4
    size, perim, coord = find_largest_region(grid1, T)
    print(f"Test 1: Size={size}, Perimeter={perim}, Coord={coord}")
    # Region: (0,0),(0,1),(1,0) - size=3, perim=8, coord=(0,0)
    assert size == 3 and perim == 8 and coord == (0, 0)
    
    # Test case 2: Same size, same perimeter, different coords
    grid2 = [
        [4, 4, 4],
        [1, 1, 1],
        [1, 1, 1]
    ]
    T = 4
    size, perim, coord = find_largest_region(grid2, T)
    print(f"Test 2: Size={size}, Perimeter={perim}, Coord={coord}")
    # Region: top row - size=3, perim=8, coord=(0,0)
    assert size == 3 and perim == 8 and coord == (0, 0)
    
    # Test case 3: Tie-breaking with perimeter
    grid3 = [
        [4, 4, 1, 1],
        [4, 4, 1, 1],
        [1, 1, 4, 4],
        [1, 1, 4, 4]
    ]
    T = 4
    size, perim, coord = find_largest_region(grid3, T)
    print(f"Test 3: Size={size}, Perimeter={perim}, Coord={coord}")
    # Two 2x2 blocks: both size=4, perim=8, coords (0,0) and (2,2)
    # (0,0) wins due to smaller coordinate
    assert size == 4 and perim == 8 and coord == (0, 0)
    
    # Test case 4: Different perimeters
    grid4 = [
        [4, 4, 4, 1],
        [4, 1, 1, 1],
        [4, 1, 1, 1],
        [1, 1, 1, 1]
    ]
    T = 4
    size, perim, coord = find_largest_region(grid4, T)
    print(f"Test 4: Size={size}, Perimeter={perim}, Coord={coord}")
    # L-shape: (0,0),(0,1),(0,2),(1,0),(2,0) - size=5, perim=12, coord=(0,0)
    assert size == 5 and perim == 12 and coord == (0, 0)
    
    print("All tests passed!")