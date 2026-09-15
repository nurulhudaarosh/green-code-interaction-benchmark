from typing import List, Sequence, Tuple, Union


class FenwickTree:
    """Fenwick Tree supporting point additions and prefix sums."""

    def __init__(self, values: Sequence[int]):
        self.n = len(values)
        self.tree = [0] * (self.n + 1)

        # Build the Fenwick tree in O(n).
        for i, value in enumerate(values, start=1):
            self.tree[i] += value
            parent = i + (i & -i)
            if parent <= self.n:
                self.tree[parent] += self.tree[i]

    def add(self, index: int, delta: int) -> None:
        """Add delta to the 0-based array position index."""
        if not 0 <= index < self.n:
            raise IndexError("index out of range")

        i = index + 1
        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, end: int) -> int:
        """
        Return the sum of values in [0, end).
        """
        if not 0 <= end <= self.n:
            raise IndexError("prefix end out of range")

        result = 0
        i = end
        while i > 0:
            result += self.tree[i]
            i -= i & -i
        return result

    def range_sum(self, left: int, right: int) -> int:
        """
        Return the inclusive sum of values in [left, right].
        """
        if not (0 <= left <= right < self.n):
            raise IndexError("invalid range")

        return self.prefix_sum(right + 1) - self.prefix_sum(left)


def process_operations(
    array: Sequence[int],
    operations: Sequence[
        Union[
            Tuple[str, int, int],
            Tuple[str, int, int, int]
        ]
    ],
) -> List[int]:
    """
    Process point replacements and inclusive range-sum queries.

    Operation formats:
        ("update", index, new_value)
        ("query", left, right)

    Indices are 0-based.

    Returns:
        A list containing the result of every query in order.
    """
    values = list(array)
    fenwick = FenwickTree(values)
    results = []

    for operation in operations:
        if not operation:
            raise ValueError("empty operation")

        operation_type = operation[0]

        if operation_type == "update":
            if len(operation) != 3:
                raise ValueError(
                    "update must be ('update', index, new_value)"
                )

            _, index, new_value = operation

            if not 0 <= index < len(values):
                raise IndexError("update index out of range")

            difference = new_value - values[index]
            values[index] = new_value
            fenwick.add(index, difference)

        elif operation_type == "query":
            if len(operation) != 3:
                raise ValueError(
                    "query must be ('query', left, right)"
                )

            _, left, right = operation

            if not (0 <= left <= right < len(values)):
                raise IndexError("invalid query range")

            results.append(fenwick.range_sum(left, right))

        else:
            raise ValueError(f"unknown operation: {operation_type}")

    return results


# Example
if __name__ == "__main__":
    array = [1, 3, 5, 7, 9]

    operations = [
        ("query", 1, 3),       # 3 + 5 + 7 = 15
        ("update", 2, 10),     # array becomes [1, 3, 10, 7, 9]
        ("query", 1, 3),       # 3 + 10 + 7 = 20
        ("query", 0, 4),       # 1 + 3 + 10 + 7 + 9 = 30
        ("update", 0, -2),     # array becomes [-2, 3, 10, 7, 9]
        ("query", 0, 1),       # -2 + 3 = 1
    ]

    print(process_operations(array, operations))
    # Output: [15, 20, 30, 1]