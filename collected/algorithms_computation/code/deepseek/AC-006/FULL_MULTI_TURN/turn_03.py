"""
Problem: Largest Threshold Region

Given a numeric grid (rectangular list of lists) and a threshold T, find the
largest 4-connected region of cells where every cell has value >= T.

Definitions:
- 4-connected: cells are connected via up, down, left, right directions
- Region: a set of cells where each cell is reachable from any other via
  4-connected path within the region
- Size: number of cells in the region
- Perimeter: count of exposed sides of the region, where a side is exposed if:
  * The neighboring cell is outside the grid bounds, OR
  * The neighboring cell has value < T (not part of the region)
- Smallest coordinate: the lexicographically smallest (row, col) pair in
  the region (row-major order: minimum row, then minimum column)

Tie-breaking rules (in priority order):
1. Larger size wins
2. If sizes are equal, larger perimeter wins
3. If both size and perimeter are equal, smaller coordinate wins

Required Output:
Returns a tuple: (size, perimeter, smallest_coordinate)
- size: int, number of cells in the region
- perimeter: int, count of exposed sides
- smallest_coordinate: tuple (row, col)

Optional Feature:
If requested, the function can also return an operation_summary field
containing a deterministic summary of the computation. This summary includes:
- Number of cells visited during flood fill (total region size)
- Number of perimeter checks performed (4 * total cells visited)
- Number of distinct regions discovered
- Number of comparison operations for tie-breaking
- Total iterations of the main loop

The operation_summary is returned as a separate value when the feature is
explicitly requested via a flag parameter.
"""

from typing import List, Tuple, Any, Optional, Dict, Union

def find_largest_region(
    grid: List[List[Any]],
    T: Any,
    return_summary: bool = False
) -> Union[Tuple[int, int, Tuple[int, int]], Tuple[int, int, Tuple[int, int], Dict[str, int]]]:
    """
    Find the largest 4-connected region with values >= T.
    
    Args:
        grid: 2D list of numeric values
        T: threshold value
        return_summary: if True, include operation_summary in output
    
    Returns:
        If return_summary is False: (size, perimeter, smallest_coordinate)
        If return_summary is True: (size, perimeter, smallest_coordinate, operation_summary)
        operation_summary is a dict with keys:
            - cells_visited: total cells in the found region
            - perimeter_checks: total neighbor checks performed (4 * cells_visited)
            - regions_discovered: number of regions found
            - tie_break_comparisons: number of comparisons made for tie-breaking
            - total_iterations: number of cells iterated in the main loop
    """
    if not grid or not grid[0]:
        if return_summary:
            return (0, 0, (0, 0), {
                'cells_visited': 0,
                'perimeter_checks': 0,
                'regions_discovered': 0,
                'tie_break_comparisons': 0,
                'total_iterations': 0
            })
        return (0, 0, (0, 0))
    
    rows = len(grid)
    cols = len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    
    # Statistics tracking
    regions_discovered = 0
    tie_break_comparisons = 0
    total_iterations = 0
    
    best_size = 0
    best_perim = 0
    best_coord = None
    
    # Directions: up, down, left, right
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for r in range(rows):
        for c in range(cols):
            total_iterations += 1
            
            if visited[r][c] or grid[r][c] < T:
                continue
            
            # Found a new region
            regions_discovered += 1
            
            # Start flood fill
            stack = [(r, c)]
            visited[r][c] = True
            size = 0
            perim = 0
            min_r, min_c = r, c
            perimeter_checks = 0
            
            while stack:
                cr, cc = stack.pop()
                size += 1
                
                # Update smallest coordinate (row-major)
                if cr < min_r or (cr == min_r and cc < min_c):
                    min_r, min_c = cr, cc
                
                # Check 4 neighbors
                for dr, dc in dirs:
                    perimeter_checks += 1
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if grid[nr][nc] >= T:
                            if not visited[nr][nc]:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                            # Internal edge - not exposed
                        else:
                            # Neighbor exists but value < T -> exposed side
                            perim += 1
                    else:
                        # Out of bounds -> exposed side
                        perim += 1
            
            # Compare with best
            if best_coord is None:
                # First region found
                best_size = size
                best_perim = perim
                best_coord = (min_r, min_c)
            else:
                # Compare: larger size wins
                tie_break_comparisons += 1
                if size > best_size:
                    best_size = size
                    best_perim = perim
                    best_coord = (min_r, min_c)
                elif size == best_size:
                    tie_break_comparisons += 1
                    # Tie on size: larger perimeter wins
                    if perim > best_perim:
                        best_perim = perim
                        best_coord = (min_r, min_c)
                    elif perim == best_perim:
                        tie_break_comparisons += 1
                        # Tie on perimeter: smaller coordinate wins
                        if min_r < best_coord[0] or (min_r == best_coord[0] and min_c < best_coord[1]):
                            best_coord = (min_r, min_c)
                            # best_size and best_perim remain the same
    
    # If no region found
    if best_coord is None:
        if return_summary:
            return (0, 0, (0, 0), {
                'cells_visited': 0,
                'perimeter_checks': 0,
                'regions_discovered': regions_discovered,
                'tie_break_comparisons': tie_break_comparisons,
                'total_iterations': total_iterations
            })
        return (0, 0, (0, 0))
    
    # Prepare result
    result = (best_size, best_perim, best_coord)
    
    if return_summary:
        # For the found region, calculate total perimeter checks
        cells_visited = best_size
        perimeter_checks = 4 * best_size  # Each cell checks 4 neighbors
        operation_summary = {
            'cells_visited': cells_visited,
            'perimeter_checks': perimeter_checks,
            'regions_discovered': regions_discovered,
            'tie_break_comparisons': tie_break_comparisons,
            'total_iterations': total_iterations
        }
        return (*result, operation_summary)
    
    return result


# Example usage and testing
if __name__ == "__main__":
    # Test grid
    grid = [
        [5, 1, 3, 4],
        [2, 4, 4, 1],
        [0, 4, 4, 2],
        [3, 1, 0, 5]
    ]
    T = 4
    
    # Without summary (original behavior)
    print("=== Without Summary (Original) ===")
    size, perim, coord = find_largest_region(grid, T)
    print(f"Size: {size}")
    print(f"Perimeter: {perim}")
    print(f"Smallest coordinate: {coord}")
    print()
    
    # With summary (new feature)
    print("=== With Summary (New Feature) ===")
    size, perim, coord, summary = find_largest_region(grid, T, return_summary=True)
    print(f"Size: {size}")
    print(f"Perimeter: {perim}")
    print(f"Smallest coordinate: {coord}")
    print("Operation Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()
    
    # Test case with multiple regions to show tie-breaking
    print("=== Multiple Regions Test ===")
    grid2 = [
        [4, 4, 1, 4],
        [4, 1, 1, 4],
        [1, 4, 4, 4],
        [1, 4, 4, 1]
    ]
    # Regions:
    # Region A: (0,0),(0,1),(1,0) - size=3, perim=8, coord=(0,0)
    # Region B: (0,3),(1,3),(2,2),(2,3),(3,1),(3,2) - size=6, perim=12, coord=(0,3)
    # Region B wins by size
    
    T = 4
    size2, perim2, coord2, summary2 = find_largest_region(grid2, T, return_summary=True)
    print(f"Size: {size2}")
    print(f"Perimeter: {perim2}")
    print(f"Smallest coordinate: {coord2}")
    print("Operation Summary:")
    for key, value in summary2.items():
        print(f"  {key}: {value}")
    print()
    
    # Verify backward compatibility: calling without return_summary works
    print("=== Backward Compatibility Test ===")
    size3, perim3, coord3 = find_largest_region(grid2, T)
    print(f"Size: {size3}, Perimeter: {perim3}, Coord: {coord3}")
    assert size3 == size2
    assert perim3 == perim2
    assert coord3 == coord2
    print("All tests passed!")