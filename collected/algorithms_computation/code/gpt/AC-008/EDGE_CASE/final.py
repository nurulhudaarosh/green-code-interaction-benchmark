"""
Mutable Range Sum Engine

Original Problem:
-----------------
Maintain an integer array under two types of operations:

1. Point replacement:
   Replace the value at a given index with a new integer.

2. Inclusive range-sum query:
   Return the sum of all values from index `left` through `right`,
   including both endpoints.

Return every range-query result in the exact order in which the
queries appear.

Key constraints:
----------------
- Array values are integers.
- Indices are zero-based and valid.
- Range endpoints are inclusive.
- There may be a large number of updates and queries.
- The solution should efficiently handle worst-case-like operation
  sequences.
- Point updates and range queries should take O(log n).
- The solution must be deterministic.
- No randomness, network access, APIs, external services, or
  human interaction.
- Only the Python standard library is used.

Required output:
----------------
Return a list containing exactly one integer for every range query,
in the same order as the queries.

Tie-breaking:
-------------
There are no competing choices or ties in this problem. Operations
are processed strictly in their given order, and query results are
returned in that same order.

Algorithm:
----------
Use a Fenwick Tree (Binary Indexed Tree).

For an update:
    delta = new_value - old_value

Apply `delta` to the Fenwick Tree in O(log n).

For a range query [left, right]:
    sum(left, right)
        = prefix_sum(right) - prefix_sum(left - 1)

Each prefix sum takes O(log n), so each range query also takes
O(log n).

Worst-case-like structure:
--------------------------
A difficult valid input can contain:
- A large array.
- Many point replacements.
- Many queries.
- Queries alternating between very small ranges and the entire
  array.
- Updates occurring at positions near the beginning and end.
- Repeated updates to the same position.
- Negative and positive values.

This stresses both Fenwick-tree update paths and prefix-sum paths
while preserving the required O(log n) complexity per operation.

Complexity:
-----------
Let n = number of array elements and m = number of operations.

- Building Fenwick tree: O(n)
- Each update: O(log n)
- Each query: O(log n)
- Total processing: O(n + m log n)
- Extra space: O(n)
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

    def add(self, index, delta):
        """Add delta to the value at zero-based index."""
        i = index + 1

        while i <= self.n:
            self.tree[i] += delta
            i += i & -i

    def prefix_sum(self, index):
        """Return sum(values[0:index + 1])."""
        if index < 0:
            return 0

        result = 0
        i = index + 1

        while i > 0:
            result += self.tree[i]
            i -= i & -i

        return result

    def range_sum(self, left, right):
        """Return the inclusive sum values[left:right + 1]."""
        if left > right:
            return 0

        return self.prefix_sum(right) - self.prefix_sum(left - 1)


def mutable_range_sum_engine(array, operations):
    """
    Process mutable-array operations.

    Supported operations:

        ("update", index, new_value)
        ("query", left, right)

    Returns:
        A list containing the result of every query in order.
    """

    values = list(array)
    fenwick = FenwickTree(values)

    results = []

    for operation in operations:
        operation_type = operation[0]

        if operation_type == "update":
            _, index, new_value = operation

            # Point replacement is converted into a point addition.
            delta = new_value - values[index]

            values[index] = new_value
            fenwick.add(index, delta)

        elif operation_type == "query":
            _, left, right = operation

            results.append(
                fenwick.range_sum(left, right)
            )

        else:
            raise ValueError(
                f"Unknown operation type: {operation_type}"
            )

    return results


# ============================================================
# TESTS
# ============================================================

def run_tests():
    """Run correctness tests, including worst-case-like structures."""

    # --------------------------------------------------------
    # Test 1: Basic queries
    # --------------------------------------------------------
    array = [1, 3, 5, 7, 9]

    operations = [
        ("query", 1, 3),
        ("query", 0, 4),
    ]

    expected = [15, 25]

    assert mutable_range_sum_engine(array, operations) == expected


    # --------------------------------------------------------
    # Test 2: Updates followed by queries
    # --------------------------------------------------------
    array = [1, 3, 5, 7, 9]

    operations = [
        ("query", 1, 3),    # 15
        ("update", 2, 10),  # [1, 3, 10, 7, 9]
        ("query", 1, 3),    # 20
        ("query", 0, 4),    # 30
        ("update", 0, -2),  # [-2, 3, 10, 7, 9]
        ("query", 0, 1),    # 1
    ]

    expected = [15, 20, 30, 1]

    assert mutable_range_sum_engine(array, operations) == expected


    # --------------------------------------------------------
    # Test 3: Single-element array
    # --------------------------------------------------------
    array = [42]

    operations = [
        ("query", 0, 0),
        ("update", 0, -10),
        ("query", 0, 0),
        ("update", 0, 100),
        ("query", 0, 0),
    ]

    expected = [42, -10, 100]

    assert mutable_range_sum_engine(array, operations) == expected


    # --------------------------------------------------------
    # Test 4: Negative values
    # --------------------------------------------------------
    array = [-5, -10, 20, -3, 8]

    operations = [
        ("query", 0, 4),
        ("query", 1, 3),
        ("update", 1, 15),
        ("query", 0, 2),
    ]

    expected = [10, 7, 30]

    assert mutable_range_sum_engine(array, operations) == expected


    # --------------------------------------------------------
    # Test 5: Repeated update of the same position
    # --------------------------------------------------------
    array = [10, 20, 30]

    operations = [
        ("query", 0, 2),
        ("update", 1, 100),
        ("query", 0, 2),
        ("update", 1, -50),
        ("query", 0, 2),
        ("update", 1, 20),
        ("query", 0, 2),
    ]

    expected = [60, 140, -30, 60]

    assert mutable_range_sum_engine(array, operations) == expected


    # --------------------------------------------------------
    # Test 6: Boundary indices
    # --------------------------------------------------------
    array = [1, 2, 3, 4, 5]

    operations = [
        ("query", 0, 0),
        ("query", 4, 4),
        ("query", 0, 4),
        ("update", 0, 100),
        ("update", 4, -100),
        ("query", 0, 0),
        ("query", 4, 4),
        ("query", 0, 4),
    ]

    expected = [1, 5, 15, 100, -100, 15]

    assert mutable_range_sum_engine(array, operations) == expected


    # --------------------------------------------------------
    # Test 7: Worst-case-like structure
    #
    # Large array + many alternating updates and queries.
    # This stresses the intended O(log n) operations.
    # --------------------------------------------------------
    n = 10_000

    array = [1] * n

    operations = []

    # Alternate updates at difficult positions with queries
    # covering small and very large ranges.
    for i in range(5_000):
        index = (i * 7919) % n

        # Replacement value varies deterministically.
        new_value = (i % 101) - 50

        operations.append(
            ("update", index, new_value)
        )

        if i % 4 == 0:
            operations.append(
                ("query", 0, n - 1)
            )
        elif i % 4 == 1:
            operations.append(
                ("query", index, index)
            )
        elif i % 4 == 2:
            left = index // 2
            right = min(n - 1, index + 100)
            operations.append(
                ("query", left, right)
            )
        else:
            operations.append(
                ("query", 0, index)
            )

    result = mutable_range_sum_engine(array, operations)

    # There must be exactly one result per query.
    query_count = sum(
        1 for op in operations if op[0] == "query"
    )

    assert len(result) == query_count


    # --------------------------------------------------------
    # Test 8: Large repeated full-range queries
    #
    # A naive implementation could repeatedly scan the entire
    # array and become O(nm). The Fenwick implementation remains
    # O(log n) per query.
    # --------------------------------------------------------
    n = 20_000

    array = list(range(1, n + 1))

    operations = [
        ("query", 0, n - 1)
        for _ in range(2_000)
    ]

    result = mutable_range_sum_engine(array, operations)

    expected_sum = n * (n + 1) // 2

    assert result == [expected_sum] * 2_000


    # --------------------------------------------------------
    # Test 9: Many updates concentrated at boundaries
    # --------------------------------------------------------
    n = 5_000

    array = [0] * n
    operations = []

    for i in range(2_000):
        if i % 2 == 0:
            operations.append(
                ("update", 0, i)
            )
        else:
            operations.append(
                ("update", n - 1, -i)
            )

        operations.append(
            ("query", 0, n - 1)
        )

    result = mutable_range_sum_engine(array, operations)

    # Validate the result independently using the same
    # deterministic operation sequence.
    expected = []
    left_value = 0
    right_value = 0

    for i in range(2_000):
        if i % 2 == 0:
            left_value = i
        else:
            right_value = -i

        expected.append(left_value + right_value)

    assert result == expected


    # --------------------------------------------------------
    # Test 10: Empty query range behavior
    #
    # This does not change normal inclusive-query behavior.
    # It only confirms the implementation handles left > right
    # deterministically as zero.
    # --------------------------------------------------------
    array = [5, 10, 15]

    operations = [
        ("query", 2, 1),
        ("query", 0, 2),
    ]

    expected = [0, 30]

    assert mutable_range_sum_engine(array, operations) == expected


    print("All tests passed.")


if __name__ == "__main__":
    run_tests()