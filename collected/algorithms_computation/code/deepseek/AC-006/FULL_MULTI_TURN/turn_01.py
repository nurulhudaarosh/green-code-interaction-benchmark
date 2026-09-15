"""
Problem: Given a numeric grid and threshold T, find the largest 4-connected region
of cells with value >= T. Return its size, perimeter, and smallest coordinate.
Ties: prefer larger perimeter, then smaller coordinate (row-major order).

Constraints:
- Grid is rectangular (list of lists of numbers)
- T is a number
- 4-connectivity: up, down, left, right

Required output: (size, perimeter, (min_row, min_col))

Algorithm:
1. Iterate through all cells.
2. If cell is unvisited and value >= T, start flood fill (BFS/DFS iteratively).
3. During flood fill:
   - Count region size.
   - Count perimeter: for each cell, each neighbor (including out-of-bounds) that
     is not in the region adds 1 to perimeter.
   - Track smallest coordinate (min_row, min_col) in the region.
4. Compare regions: larger size wins; if tie, larger perimeter wins; if tie,
   smaller coordinate wins.
5. Return result.

Implementation: deterministic, iterative flood fill using stack, standard library only.
"""

from typing import List, Tuple, Optional, Any

def find_largest_region(grid: List[List[Any]], T: Any) -> Tuple[int, int, Tuple[int, int]]:
    if not grid or not grid[0]:
        return (0, 0, (0, 0))
    
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    best_size = -1
    best_perim = -1
    best_coord = (rows, cols)  # large sentinel
    
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
                
                # Update smallest coordinate
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
                        else:
                            # Neighbor exists but value < T -> boundary
                            perim += 1
                    else:
                        # Out of bounds -> boundary
                        perim += 1
            
            # Compare with best
            if (size > best_size or
                (size == best_size and perim > best_perim) or
                (size == best_size and perim == best_perim and
                 (min_r < best_coord[0] or (min_r == best_coord[0] and min_c < best_coord[1])))):
                best_size = size
                best_perim = perim
                best_coord = (min_r, min_c)
    
    return (best_size, best_perim, best_coord)


# Example usage (for testing, not part of final answer)
if __name__ == "__main__":
    # Example grid
    grid = [
        [5, 1, 3],
        [2, 4, 4],
        [0, 4, 4]
    ]
    T = 4
    
    size, perim, coord = find_largest_region(grid, T)
    print(f"Size: {size}, Perimeter: {perim}, Smallest coordinate: {coord}")
    # Expected: region of 4s at (1,1),(1,2),(2,1),(2,2) -> size=4, perim=8, coord=(1,1)