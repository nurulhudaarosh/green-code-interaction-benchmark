"""
Problem: Mutable Range Sum Engine

Maintain an integer array under two types of operations:
1. Point replacement: replace the value at a given index.
2. Inclusive range-sum query: return the sum of all values from index
   left through right, inclusive.

Return every range-query result in the same order as the queries appear.

Key constraints:
- The array contains integers.
- Point updates and range queries may be numerous, so an O(n) operation
  for every update/query is too slow.
- Indices are assumed to be valid for the array.
- Range boundaries are inclusive.
- The solution must be deterministic.
- Use only Python's standard library.

Required output:
- A list containing exactly one integer for each range-sum query,
  in query order.

Algorithm:
Use a Fenwick tree (Binary Indexed Tree).
- Build the tree from the initial array.
- A point replacement is handled by calculating the difference between
  the new and old values, then applying that difference to the Fenwick tree.
- A prefix sum is calculated in O(log n).
- A range sum [left, right] is:
      prefix_sum(right) - prefix_sum(left - 1)
- Therefore, both updates and queries take O(log n).

Time complexity:
- Building: O(n log n) with the implementation below.
- Each update: O(log n)
- Each range query: O(log n)
- Extra space: O(n)
"""


class FenwickTree:
    def __init__(self, values):
        self.n = len(values)
        self.tree = [0] * (self.n + 1)

        # Build the Fenwick tree.
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
        """
        Return sum of values from index 0 through index, inclusive.
        Returns 0 when index < 0.
        """
        if index < 0:
            return 0

        result = 0
        i = index + 1

        while i > 0:
            result += self.tree[i]
            i -= i & -i

        return result

    def range_sum(self, left, right):
        """Return the inclusive sum of values from left through right."""
        if left > right:
            return 0

        return self.prefix_sum(right) - self.prefix_sum(left - 1)


def mutable_range_sum_engine(array, operations):
    """
    Process point replacements and inclusive range-sum queries.

    Operation formats:
        ("update", index, new_value)
        ("query", left, right)

    Returns:
        List of query results in their original order.
    """
    values = list(array)
    fenwick = FenwickTree(values)

    results = []

    for operation in operations:
        operation_type = operation[0]

        if operation_type == "update":
            _, index, new_value = operation

            # Calculate the change from the old value to the new value.
            delta = new_value - values[index]

            # Update both the original-value array and Fenwick tree.
            values[index] = new_value
            fenwick.add(index, delta)

        elif operation_type == "query":
            _, left, right = operation

            results.append(fenwick.range_sum(left, right))

        else:
            raise ValueError(f"Unknown operation type: {operation_type}")

    return results


# ---------------------------------------------------------
# Example
# ---------------------------------------------------------

if __name__ == "__main__":
    array = [1, 3, 5, 7, 9]

    operations = [
        ("query", 1, 3),   # 3 + 5 + 7 = 15
        ("update", 2, 10), # [1, 3, 10, 7, 9]
        ("query", 1, 3),   # 3 + 10 + 7 = 20
        ("query", 0, 4),   # 1 + 3 + 10 + 7 + 9 = 30
        ("update", 0, -2),
        ("query", 0, 1),   # -2 + 3 = 1
    ]

    print(mutable_range_sum_engine(array, operations))

    # Expected output:
    # [15, 20, 30, 1]