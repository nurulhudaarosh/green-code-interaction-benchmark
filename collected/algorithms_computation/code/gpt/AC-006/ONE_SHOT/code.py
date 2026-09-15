# Largest 4-Connected Region Above Threshold
# Uses iterative flood fill and counts every exposed side.
# Standard library only.

def largest_region(grid, T):
    """
    Find the largest 4-connected region containing cells with value >= T.

    Tie-breaking:
        1. Larger region size
        2. Larger perimeter
        3. Smaller lexicographical coordinate (row, column)

    Returns:
        (size, perimeter, smallest_coordinate)

    For an empty grid or no qualifying cells:
        (0, 0, None)
    """

    if not grid or not grid[0]:
        return (0, 0, None)

    rows = len(grid)
    cols = len(grid[0])

    visited = [[False] * cols for _ in range(rows)]

    # Up, down, left, right
    directions = (
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
    )

    best_size = 0
    best_perimeter = 0
    best_coordinate = None

    for r in range(rows):
        for c in range(cols):

            # Skip cells that are not part of a valid region.
            if visited[r][c] or grid[r][c] < T:
                continue

            # Start iterative flood fill.
            stack = [(r, c)]
            visited[r][c] = True

            size = 0
            perimeter = 0
            smallest_coordinate = (r, c)

            while stack:
                cr, cc = stack.pop()

                size += 1

                if (cr, cc) < smallest_coordinate:
                    smallest_coordinate = (cr, cc)

                # Check all four sides.
                for dr, dc in directions:
                    nr = cr + dr
                    nc = cc + dc

                    # Outside the grid -> exposed side.
                    if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                        perimeter += 1
                        continue

                    # Neighbor below threshold -> exposed side.
                    if grid[nr][nc] < T:
                        perimeter += 1
                        continue

                    # Valid neighboring cell -> continue flood fill.
                    if not visited[nr][nc]:
                        visited[nr][nc] = True
                        stack.append((nr, nc))

            # Compare this region with the best region.
            is_better = False

            if size > best_size:
                is_better = True
            elif size == best_size:
                if perimeter > best_perimeter:
                    is_better = True
                elif perimeter == best_perimeter:
                    if (
                        best_coordinate is None
                        or smallest_coordinate < best_coordinate
                    ):
                        is_better = True

            if is_better:
                best_size = size
                best_perimeter = perimeter
                best_coordinate = smallest_coordinate

    return (best_size, best_perimeter, best_coordinate)


# Example
if __name__ == "__main__":
    grid = [
        [5, 5, 1, 2],
        [5, 6, 1, 3],
        [2, 5, 5, 3],
        [1, 1, 4, 4],
    ]

    T = 5

    print(largest_region(grid, T))