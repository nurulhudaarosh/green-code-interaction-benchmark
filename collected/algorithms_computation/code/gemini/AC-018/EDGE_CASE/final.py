def multiply_polynomials(p: list[int], q: list[int]) -> list[int]:
    """
    Multiplies two integer polynomials using direct deterministic convolution.
    Handles negative values, repeated coefficients, zeros, and multiple index-sum ties.
    
    :param p: Coefficient list of first polynomial [a_0, a_1, ..., a_m]
    :param q: Coefficient list of second polynomial [b_0, b_1, ..., b_n]
    :return: Coefficient list of the exact product polynomial
    """
    if not p or not q:
        return []

    len_p = len(p)
    len_q = len(q)

    # Output size is deterministically (deg(P) + deg(Q) + 1) = len_p + len_q - 1
    result = [0] * (len_p + len_q - 1)

    # Accumulate products into corresponding degree positions k = i + j
    for i in range(len_p):
        for j in range(len_q):
            result[i + j] += p[i] * q[j]

    return result


# Unit Tests
def run_tests():
    # 1. Base Case (Original test)
    # (1 - 2x + 3x^2) * (4 + 5x) = 4 - 3x + 2x^2 + 15x^3
    assert multiply_polynomials([1, -2, 3], [4, 5]) == [4, -3, 2, 15]

    # 2. Repeated Values (Repeated coefficients across inputs)
    # (2 + 2x + 2x^2) * (2 + 2x) = 4 + 8x + 8x^2 + 4x^3
    assert multiply_polynomials([2, 2, 2], [2, 2]) == [4, 8, 8, 4]

    # 3. Multiple Index-Sum Ties (Multiple (i, j) pairs sum to the same k)
    # P(x) = 1 - 1x + 1x^2, Q(x) = 1 + 1x + 1x^2
    # k=2 terms: (1*1) + (-1*1) + (1*1) = 1
    # Result: 1 + 0x + 1x^2 + 0x^3 + 1x^4
    assert multiply_polynomials([1, -1, 1], [1, 1, 1]) == [1, 0, 1, 0, 1]

    # 4. Trailing and Internal Zeros
    # (1 + 0x + 2x^2) * (0 + 3x) = 0 + 3x + 0x^2 + 6x^3
    assert multiply_polynomials([1, 0, 2], [0, 3]) == [0, 3, 0, 6]

    # 5. Empty and Single-Element Inputs
    assert multiply_polynomials([], [1, 2, 3]) == []
    assert multiply_polynomials([-5], [3]) == [-15]

    print("All polynomial multiplication tests passed successfully!")

if __name__ == "__main__":
    run_tests()