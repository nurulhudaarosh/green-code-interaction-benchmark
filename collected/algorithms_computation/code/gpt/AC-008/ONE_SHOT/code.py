from typing import List, Tuple, Union


# Operation formats:
#   ("update", index, new_value)
#   ("query", left, right)
Operation = Tuple[str, int, int]


def minimum_fenwick_sum_operations(
    arr: List[int],
    operations: List[Operation],
) -> List[int]:
    """
    Maintain an integer array under:
      - point replacement: ("update", index, new_value)
      - inclusive range sum: ("query", left, right)

    Indices are 0-based.

    Returns:
        A list containing the result of every range-sum query
        in the order the queries occur.

    Raises:
        ValueError: for invalid operation types or invalid indices/ranges.
        TypeError: for invalid input types.
    """

    if not isinstance(arr, list):
        raise TypeError("arr must be a list")

    n = len(arr)

    if any(not isinstance(x, int) for x in arr):
        raise TypeError("all array values must be integers")

    # Fenwick tree uses 1-based indexing.
    bit = [0] * (n + 1)

    def add(index: int, delta: int) -> None:
        """Add delta to the 0-based array index."""
        i = index + 1
        while i <= n:
            bit[i] += delta
            i += i & -i

    def prefix_sum(index: int) -> int:
        """
        Return sum of arr[0:index+1].
        If index < 0, return 0.
        """
        if index < 0:
            return 0

        total = 0
        i = index + 1

        while i > 0:
            total += bit[i]
            i -= i & -i

        return total

    # Build the Fenwick tree in O(n).
    for i, value in enumerate(arr):
        bit[i + 1] += value
        parent = (i + 1) + ((i + 1) & -(i + 1))

        if parent <= n:
            bit[parent] += bit[i + 1]

    values = arr.copy()
    results: List[int] = []

    for operation in operations:
        if not isinstance(operation, tuple) or len(operation) != 3:
            raise ValueError(
                "Each operation must be a 3-item tuple"
            )

        op, x, y = operation

        if not isinstance(op, str):
            raise TypeError("Operation type must be a string")

        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError("Operation indices/values must be integers")

        if op == "update":
            index = x
            new_value = y

            if not 0 <= index < n:
                raise ValueError("Update index out of range")

            delta = new_value - values[index]
            values[index] = new_value
            add(index, delta)

        elif op == "query":
            left = x
            right = y

            if not 0 <= left <= right < n:
                raise ValueError("Invalid query range")

            result = prefix_sum(right) - prefix_sum(left - 1)
            results.append(result)

        else:
            raise ValueError(
                f"Unknown operation: {op!r}. "
                "Expected 'update' or 'query'."
            )

    return results


# ------------------------------------------------------------
# Example
# ------------------------------------------------------------

arr = [1, 2, 3, 4, 5]

operations = [
    ("query", 1, 3),    # 2 + 3 + 4 = 9
    ("update", 2, 10),  # [1, 2, 10, 4, 5]
    ("query", 1, 3),    # 2 + 10 + 4 = 16
    ("update", 0, -5),  # [-5, 2, 10, 4, 5]
    ("query", 0, 2),    # -5 + 2 + 10 = 7
]

print(minimum_fenwick_sum_operations(arr, operations))
# Output: [9, 16, 7]


# ------------------------------------------------------------
# Basic deterministic tests
# ------------------------------------------------------------

def _run_tests() -> None:
    # Normal case
    assert minimum_fenwick_sum_operations(
        [1, 2, 3, 4, 5],
        [
            ("query", 0, 4),
            ("update", 2, 10),
            ("query", 1, 3),
        ],
    ) == [15, 16]

    # Single-element array
    assert minimum_fenwick_sum_operations(
        [7],
        [
            ("query", 0, 0),
            ("update", 0, -3),
            ("query", 0, 0),
        ],
    ) == [7, -3]

    # Negative values
    assert minimum_fenwick_sum_operations(
        [-5, -2, 10, -3],
        [
            ("query", 0, 3),
            ("query", 1, 2),
            ("update", 1, 8),
            ("query", 0, 2),
        ],
    ) == [0, 8, 13]

    # Replacing a value with the same value
    assert minimum_fenwick_sum_operations(
        [4, 4, 4],
        [
            ("update", 1, 4),
            ("query", 0, 2),
        ],
    ) == [12]

    # Empty array: no queries means empty result
    assert minimum_fenwick_sum_operations([], []) == []

    print("All tests passed.")


if __name__ == "__main__":
    _run_tests()