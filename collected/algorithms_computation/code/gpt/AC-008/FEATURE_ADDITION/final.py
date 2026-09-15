from typing import List, Sequence, Tuple, Union, Dict, Any


Operation = Tuple[str, int, int]


class FenwickTree:
    """Fenwick tree with deterministic operation counting."""

    def __init__(self, values: Sequence[int]) -> None:
        self.n = len(values)
        self.tree = [0] * (self.n + 1)

        # Number of major Fenwick computational steps.
        self.major_operations = 0

        # O(n) Fenwick construction.
        for i, value in enumerate(values, start=1):
            self.tree[i] += value

            parent = i + (i & -i)
            if parent <= self.n:
                self.tree[parent] += self.tree[i]

    def add(self, index: int, delta: int) -> None:
        """Add delta to a zero-based array index."""
        if not 0 <= index < self.n:
            raise IndexError("array index out of range")

        i = index + 1

        while i <= self.n:
            self.tree[i] += delta

            # One Fenwick update step.
            self.major_operations += 1

            i += i & -i

    def prefix_sum(self, end: int) -> int:
        """Return the sum of values in [0, end)."""
        if not 0 <= end <= self.n:
            raise IndexError("prefix endpoint out of range")

        total = 0
        i = end

        while i > 0:
            total += self.tree[i]

            # One Fenwick prefix-sum step.
            self.major_operations += 1

            i -= i & -i

        return total

    def range_sum(self, left: int, right: int) -> int:
        """Return the inclusive sum of values in [left, right]."""
        if not (0 <= left <= right < self.n):
            raise IndexError("invalid range")

        return (
            self.prefix_sum(right + 1)
            - self.prefix_sum(left)
        )


def process_operations(
    initial: Sequence[int],
    operations: Sequence[Operation],
    include_operation_summary: bool = False,
) -> Union[List[int], Dict[str, Any]]:
    """
    Maintain an integer array under point replacements and
    inclusive range-sum queries.

    Operation format:
        ("update", index, new_value)
        ("query", left, right)

    Original behavior:
        include_operation_summary=False
        -> returns List[int]

    Extended behavior:
        include_operation_summary=True
        -> returns:
           {
               "results": List[int],
               "operation_summary": {
                   "major_operations": int
               }
           }
    """

    values = list(initial)
    fenwick = FenwickTree(values)
    results: List[int] = []

    for operation in operations:
        if len(operation) != 3:
            raise ValueError(
                "each operation must contain exactly 3 values"
            )

        op, a, b = operation

        if op == "update":
            index = a
            new_value = b

            if not 0 <= index < len(values):
                raise IndexError("array index out of range")

            # Convert replacement into a point addition.
            delta = new_value - values[index]

            values[index] = new_value
            fenwick.add(index, delta)

        elif op == "query":
            left = a
            right = b

            results.append(
                fenwick.range_sum(left, right)
            )

        else:
            raise ValueError(f"unknown operation: {op!r}")

    # Preserve the original output exactly when the feature
    # is disabled or not requested.
    if not include_operation_summary:
        return results

    return {
        "results": results,
        "operation_summary": {
            "major_operations": fenwick.major_operations
        },
    }


# ---------------------------------------------------------
# Example
# ---------------------------------------------------------

if __name__ == "__main__":
    initial = [1, 2, 3, 4, 5]

    operations = [
        ("query", 1, 3),   # 2 + 3 + 4 = 9
        ("update", 2, 10), # [1, 2, 10, 4, 5]
        ("query", 1, 3),   # 2 + 10 + 4 = 16
        ("query", 0, 4),   # 1 + 2 + 10 + 4 + 5 = 22
    ]

    # Original behavior remains unchanged.
    print(process_operations(initial, operations))
    # [9, 16, 22]

    # New optional behavior.
    print(
        process_operations(
            initial,
            operations,
            include_operation_summary=True,
        )
    )
    # {
    #     'results': [9, 16, 22],
    #     'operation_summary': {
    #         'major_operations': ...
    #     }
    # }