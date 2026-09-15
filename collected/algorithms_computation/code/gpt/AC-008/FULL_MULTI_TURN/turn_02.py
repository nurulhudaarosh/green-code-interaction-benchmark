"""
Mutable Range Sum Engine

Problem:
Maintain an integer array under:
1. Point replacement operations:
       ("update", index, new_value)

2. Inclusive range-sum queries:
       ("query", left, right)

Return exactly the results of all query operations, in the same
order in which the queries appear.

Expected behavior:
- Updates replace the existing value at an index.
- Queries return the inclusive sum array[left:right + 1].
- Operations are processed strictly from left to right.
- Results contain one integer for each query and nothing else.
- No randomness or external services are used.
- A Fenwick tree provides O(log n) updates and prefix sums.
- Initial Fenwick-tree construction is O(n).
- There is no tie-breaking decision for sums; deterministic behavior
  comes from preserving the exact input operation order.
"""


class FenwickTree:
    """Fenwick Tree supporting point additions and prefix sums."""

    def __init__(self, values):
        self.n = len(values)
        self.tree = [0] * (self.n + 1)

        # O(n) Fenwick-tree construction.
        for i, value in enumerate(values, start=1):
            self.tree[i] += value

            parent = i + (i & -i)
            if parent <= self.n:
                self.tree[parent] += self.tree[i]

    def update(self, index, delta):
        """Add delta to the value at 0-based index."""
        i = index + 1

        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, index):
        """Return the sum of values from index 0 through index."""
        if index < 0:
            return 0

        total = 0
        i = index + 1

        while i > 0:
            total += self.tree[i]
            i -= i & -i

        return total

    def range_sum(self, left, right):
        """Return the inclusive sum from left through right."""
        return (
            self.prefix_sum(right)
            - self.prefix_sum(left - 1)
        )


def mutable_range_sum_engine(array, operations):
    """
    Process point replacements and inclusive range-sum queries.

    Returns:
        Exactly one integer for every query operation, in input order.
    """

    values = list(array)
    fenwick = FenwickTree(values)

    results = []

    # Process operations deterministically in their original order.
    for operation in operations:
        operation_type = operation[0]

        if operation_type == "update":
            _, index, new_value = operation

            old_value = values[index]
            delta = new_value - old_value

            # Replace the current value.
            values[index] = new_value

            # Reflect the replacement in the Fenwick tree.
            fenwick.update(index, delta)

        elif operation_type == "query":
            _, left, right = operation

            # Inclusive range sum.
            results.append(fenwick.range_sum(left, right))

        else:
            raise ValueError(
                f"Unknown operation type: {operation_type}"
            )

    # Return exactly the required result.
    return results


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def run_tests():
    # Small example demonstrating the required behavior.
    array = [1, 2, 3]
    operations = [
        ("query", 0, 2),   # 1 + 2 + 3 = 6
        ("update", 1, 5),
        ("query", 0, 2),   # 1 + 5 + 3 = 9
    ]

    assert mutable_range_sum_engine(array, operations) == [6, 9]

    # Single-element range.
    array = [10, 20, 30]
    operations = [
        ("query", 1, 1),
    ]

    assert mutable_range_sum_engine(array, operations) == [20]

    # Full range.
    array = [1, 2, 3, 4, 5]
    operations = [
        ("query", 0, 4),
    ]

    assert mutable_range_sum_engine(array, operations) == [15]

    # Negative values.
    array = [-5, 10, -3, 8]
    operations = [
        ("query", 0, 3),
        ("update", 2, 5),
        ("query", 1, 3),
    ]

    assert mutable_range_sum_engine(array, operations) == [10, 23]

    # Replacing a value with the same value.
    array = [4, 6, 8]
    operations = [
        ("update", 1, 6),
        ("query", 0, 2),
    ]

    assert mutable_range_sum_engine(array, operations) == [18]

    # Multiple updates at the same position.
    array = [1, 2, 3]
    operations = [
        ("update", 0, 10),
        ("update", 0, -5),
        ("update", 0, 100),
        ("query", 0, 0),
        ("query", 0, 2),
    ]

    assert mutable_range_sum_engine(array, operations) == [100, 105]

    # Queries must preserve their original order.
    array = [5, 5]
    operations = [
        ("query", 0, 0),   # 5
        ("update", 0, 10),
        ("query", 0, 0),   # 10
        ("query", 0, 1),   # 15
    ]

    assert mutable_range_sum_engine(array, operations) == [5, 10, 15]

    # No operations means no query results.
    assert mutable_range_sum_engine([1, 2, 3], []) == []


if __name__ == "__main__":
    # Tests are intentionally silent when successful.
    # The program does not print extra output that could violate
    # the "exactly the required result" requirement.
    run_tests()