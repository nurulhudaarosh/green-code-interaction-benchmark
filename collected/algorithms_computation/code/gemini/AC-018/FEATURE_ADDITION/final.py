from typing import List, Dict, Any, Union

def multiply_polynomials(
    a: List[int], 
    b: List[int], 
    include_summary: bool = False
) -> Union[List[int], Dict[str, Any]]:
    """
    Multiplies two integer polynomials using direct discrete convolution.
    Optionally returns a computational operation summary.

    :param a: Coefficient list of the first polynomial [a0, a1, ...]
    :param b: Coefficient list of the second polynomial [b0, b1, ...]
    :param include_summary: If True, returns dict with coefficients and operation_summary.
                            If False, returns only the coefficient list.
    :return: List of product coefficients or a dictionary with coefficients and metadata.
    """
    # Handle empty polynomial edge cases
    if not a or not b:
        coefficients = []
        summary = {
            "input_degrees": (-1, -1),
            "output_degree": -1,
            "multiplications": 0,
            "additions": 0,
            "is_empty": True
        }
        return {"coefficients": coefficients, "operation_summary": summary} if include_summary else coefficients

    m, n = len(a), len(b)
    result_len = m + n - 1
    result = [0] * result_len

    # Track operational counts
    multiplication_count = 0
    addition_count = 0

    for i in range(m):
        for j in range(n):
            result[i + j] += a[i] * b[j]
            multiplication_count += 1
            addition_count += 1

    if include_summary:
        summary = {
            "input_degrees": (m - 1, n - 1),
            "output_degree": result_len - 1,
            "multiplications": multiplication_count,
            "additions": addition_count,
            "is_empty": False
        }
        return {
            "coefficients": result,
            "operation_summary": summary
        }

    return result


# Example Usage & Verification:
if __name__ == "__main__":
    poly1 = [1, 2, -3]  # 1 + 2x - 3x^2
    poly2 = [-4, 5]     # -4 + 5x

    # 1. Default Behavior (Backwards Compatible)
    coeffs_only = multiply_polynomials(poly1, poly2)
    print("Coefficients only:", coeffs_only)
    # Output: [-4, -3, 22, -15]

    # 2. Summary Request Enabled
    full_result = multiply_polynomials(poly1, poly2, include_summary=True)
    print("\nWith Summary Output:")
    print("Coefficients:", full_result["coefficients"])
    print("Summary:", full_result["operation_summary"])