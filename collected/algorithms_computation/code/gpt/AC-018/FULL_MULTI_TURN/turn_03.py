id="58241"
# Exact Polynomial Product
#
# Original problem:
# Given two integer polynomials represented by coefficient arrays in
# ascending order of degree, multiply them exactly and return the
# coefficient array of the product. Coefficients may be negative.
#
# Original required output:
# - A coefficient array containing the exact coefficients of A(x) * B(x).
# - Coefficients are returned in ascending degree order, with the constant
#   coefficient first.
# - If either input polynomial is empty, return [].
#
# Existing requirements preserved:
# - Use direct coefficient convolution.
# - Deterministic computation.
# - No randomness, network access, APIs, external services, or human input.
# - The quadratic O(n*m) computation is practical under the stated
#   constraints.
# - No unrelated output fields are added unless the optional feature below
#   is explicitly requested.
#
# New optional feature:
# When include_operation_summary=True, return a dictionary containing:
#   "coefficients": the original required coefficient array
#   "operation_summary": a deterministic summary containing the number of
#                         major convolution operations performed.
#
# The operation count is defined as the number of coefficient-pair
# multiplications, which is exactly len(a) * len(b) for non-empty inputs.
# For an empty input, no convolution operations are performed, so the count
# is 0.
#
# When include_operation_summary=False (the default), the original behavior
# is preserved exactly: only the coefficient array is returned.
#
# Algorithm:
# For every coefficient pair a[i], b[j], compute a[i] * b[j] and add it
# to result[i + j]. This is direct coefficient convolution.
#
# Time: O(n * m)
# Space: O(n + m) for the output.
#
# Deterministic tie handling:
# There is no selection/tie-breaking step in polynomial multiplication.
# Every coefficient pair has exactly one destination index i + j, and the
# iteration order is fixed.

from typing import List, Union, Dict, Any


def multiply_polynomials(
    a: List[int],
    b: List[int],
    include_operation_summary: bool = False
) -> Union[List[int], Dict[str, Any]]:
    """Multiply two integer polynomials exactly.

    By default, returns only the original coefficient array.

    If include_operation_summary is True, returns:
        {
            "coefficients": [...],
            "operation_summary": {
                "convolution_operations": ...
            }
        }
    """
    if not a or not b:
        coefficients = []

        if include_operation_summary:
            return {
                "coefficients": coefficients,
                "operation_summary": {
                    "convolution_operations": 0
                }
            }

        return coefficients

    result = [0] * (len(a) + len(b) - 1)

    # Direct coefficient convolution.
    operation_count = 0

    for i in range(len(a)):
        for j in range(len(b)):
            result[i + j] += a[i] * b[j]
            operation_count += 1

    if include_operation_summary:
        return {
            "coefficients": result,
            "operation_summary": {
                "convolution_operations": operation_count
            }
        }

    return result


# Deterministic tests
def run_tests() -> None:
    # Original behavior remains unchanged when the feature is disabled.
    assert multiply_polynomials([1, 2], [3, 4]) == [3, 10, 8]

    # Negative coefficients.
    assert multiply_polynomials([2, -3], [-1, 4]) == [-2, 11, -12]

    # Repeated values.
    assert multiply_polynomials([2, 2, 2], [2, 2, 2]) == [
        4, 8, 12, 8, 4
    ]

    # Mixed signs.
    assert multiply_polynomials([1, -1, 1], [-2, 3]) == [
        -2, 5, -5, 3
    ]

    # Zero polynomial.
    assert multiply_polynomials([0, 0], [5, -2, 7]) == [
        0, 0, 0, 0
    ]

    # Single coefficients.
    assert multiply_polynomials([7], [-3]) == [-21]

    # Empty inputs preserve original behavior.
    assert multiply_polynomials([], [1, 2]) == []
    assert multiply_polynomials([1, 2], []) == []

    # Optional operation summary.
    summary_result = multiply_polynomials(
        [1, 2],
        [3, 4],
        include_operation_summary=True
    )

    assert summary_result == {
        "coefficients": [3, 10, 8],
        "operation_summary": {
            "convolution_operations": 4
        }
    }

    # Operation count for 3 * 3 coefficient pairs.
    repeated_summary = multiply_polynomials(
        [2, 2, 2],
        [2, 2, 2],
        include_operation_summary=True
    )

    assert repeated_summary["coefficients"] == [4, 8, 12, 8, 4]
    assert repeated_summary["operation_summary"] == {
        "convolution_operations": 9
    }

    # Empty input performs zero operations.
    empty_summary = multiply_polynomials(
        [],
        [1, 2, 3],
        include_operation_summary=True
    )

    assert empty_summary == {
        "coefficients": [],
        "operation_summary": {
            "convolution_operations": 0
        }
    }

    # Determinism.
    first = multiply_polynomials(
        [3, -1, 3],
        [-2, 4],
        include_operation_summary=True
    )
    second = multiply_polynomials(
        [3, -1, 3],
        [-2, 4],
        include_operation_summary=True
    )

    assert first == second


if __name__ == "__main__":
    run_tests()