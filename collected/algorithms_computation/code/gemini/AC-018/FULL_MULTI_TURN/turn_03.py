from typing import Union, Tuple, Dict, Any

def multiply_polynomials(
    poly1: list[int], 
    poly2: list[int], 
    include_summary: bool = False
) -> Union[list[int], Tuple[list[int], Dict[str, int]]]:
    """
    Multiplies two polynomials represented by lists of integer coefficients
    using direct discrete convolution.

    :param poly1: Coefficients of the first polynomial [a0, a1, ...].
    :param poly2: Coefficients of the second polynomial [b0, b1, ...].
    :param include_summary: If True, returns a tuple (coefficients, operation_summary).
    :return: Either canonical coefficient list or tuple with operation_summary.
    """
    # Track major operations made during the algorithm execution
    multiplications = 0
    additions = 0
    trim_steps = 0

    # Handle empty or zero inputs
    if not poly1 or not poly2:
        result = [0]
        if include_summary:
            summary = {
                "multiplications": 0,
                "additions": 0,
                "trim_steps": 0
            }
            return result, summary
        return result

    n = len(poly1)
    m = len(poly2)
    
    # Direct coefficient convolution
    result = [0] * (n + m - 1)
    for i in range(n):
        for j in range(m):
            result[i + j] += poly1[i] * poly2[j]
            multiplications += 1
            additions += 1

    # Trim trailing zero coefficients to preserve canonical degree representation
    while len(result) > 1 and result[-1] == 0:
        result.pop()
        trim_steps += 1

    if include_summary:
        summary = {
            "multiplications": multiplications,
            "additions": additions,
            "trim_steps": trim_steps
        }
        return result, summary

    return result


if __name__ == "__main__":
    p1 = [1, 2, -3]
    p2 = [-2, 1]

    # Standard usage (unchanged)
    print("Standard:", multiply_polynomials(p1, p2))
    # Output: [-2, -3, 8, -3]

    # Enhanced usage with operation summary
    coeffs, summary = multiply_polynomials(p1, p2, include_summary=True)
    print("Coefficients:", coeffs)
    print("Summary:", summary)
    # Output:
    # Coefficients: [-2, -3, 8, -3]
    # Summary: {'multiplications': 6, 'additions': 6, 'trim_steps': 0}