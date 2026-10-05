from typing import List

def multiply_polynomials(a: List[int], b: List[int]) -> List[int]:
    """
    Multiply two integer polynomials represented in highest-to-lowest degree order.
    Returns the product polynomial coefficient list in highest-to-lowest order.
    """
    if not a or not b:
        return []

    # Degree of input polynomials
    deg_a = len(a) - 1
    deg_b = len(b) - 1

    # Result degree is deg_a + deg_b, so length is deg_a + deg_b + 1
    result_len = deg_a + deg_b + 1
    result = [0] * result_len

    # Direct convolution
    for i, ca in enumerate(a):
        if ca == 0:
            continue
        # Degree of current coefficient from a
        deg_from_a = deg_a - i
        for j, cb in enumerate(b):
            if cb == 0:
                continue
            deg_from_b = deg_b - j
            deg = deg_from_a + deg_from_b
            # Map degree to index in highest-to-lowest result
            idx = (deg_a + deg_b) - deg
            result[idx] += ca * cb

    # Remove leading zeros, but keep at least one coefficient
    while len(result) > 1 and result[0] == 0:
        result.pop(0)

    return result


if __name__ == "__main__":
    # Example 1: (2x + 3) * (4x - 5) = 8x^2 + 2x - 15
    p1 = [2, 3]      # 2x + 3
    p2 = [4, -5]     # 4x - 5
    print(multiply_polynomials(p1, p2))  # [8, 2, -15]

    # Example 2: (x^2 - 1) * (x + 2) = x^3 + 2x^2 - x - 2
    p3 = [1, 0, -1]  # x^2 - 1
    p4 = [1, 2]      # x + 2
    print(multiply_polynomials(p3, p4))  # [1, 2, -1, -2]

    # Example 3: zero polynomial
    print(multiply_polynomials([0], [1, 2, 3]))  # [0]

    # Example 4: negative coefficients
    p5 = [-1, 2, -3]
    p6 = [4, -5]
    print(multiply_polynomials(p5, p6))  # [-4, 13, -22, 15]