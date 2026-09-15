import unittest

def matrix_chain_order(p, include_summary=False):
    """
    Computes minimum scalar multiplication cost and optimal parenthesization
    for a matrix chain given dimensions sequence p.
    
    Deterministic Tie-Breaking:
    Strictly selects the smallest split index k on cost ties.
    
    :param p: List of dimensions where matrix A_i has dimensions p[i-1] x p[i].
    :param include_summary: If True, returns dict with 'cost', 'parenthesization',
                            and 'operation_summary'. Otherwise returns (cost, parenthesization).
    """
    if not p or len(p) < 2:
        res_cost, res_str = 0, ""
        if include_summary:
            return {
                "cost": res_cost,
                "parenthesization": res_str,
                "operation_summary": {"matrices_count": 0, "split_evaluations": 0}
            }
        return res_cost, res_str

    n = len(p) - 1  # Number of matrices

    if n == 1:
        res_cost, res_str = 0, "A1"
        if include_summary:
            return {
                "cost": res_cost,
                "parenthesization": res_str,
                "operation_summary": {"matrices_count": 1, "split_evaluations": 0}
            }
        return res_cost, res_str

    # m[i][j]: minimum cost to multiply A_i...A_j
    # s[i][j]: optimal split index k for subchain A_i...A_j
    m = [[0] * (n + 1) for _ in range(n + 1)]
    s = [[0] * (n + 1) for _ in range(n + 1)]

    split_evaluations_count = 0

    # Interval DP over chain length l
    for l in range(2, n + 1):
        for i in range(1, n - l + 2):
            j = i + l - 1
            m[i][j] = float('inf')
            
            # Iterate k sequentially from i to j-1
            for k in range(i, j):
                split_evaluations_count += 1
                cost = m[i][k] + m[k + 1][j] + p[i - 1] * p[k] * p[j]
                
                # Strict inequality strictly enforces picking the smallest k on tie
                if cost < m[i][j]:
                    m[i][j] = cost
                    s[i][j] = k

    # Construct parenthesization string
    def build_string(i, j):
        if i == j:
            return f"A{i}"
        k = s[i][j]
        left = build_string(i, k)
        right = build_string(k + 1, j)
        return f"({left}{right})"

    min_cost = m[1][n]
    parenthesization = build_string(1, n)

    if include_summary:
        return {
            "cost": min_cost,
            "parenthesization": parenthesization,
            "operation_summary": {
                "matrices_count": n,
                "split_evaluations": split_evaluations_count,
                "subproblems_solved": (n * (n - 1)) // 2
            }
        }

    return min_cost, parenthesization


# Unit Test Suite for Difficult Cases
class TestMatrixChainPlanner(unittest.TestCase):

    def test_repeated_dimensions_ties(self):
        """
        4 square matrices of identical size [10, 10, 10, 10, 10].
        Splits k=1 and k=3 both yield minimal cost 2000.
        Smallest index k=1 MUST be selected -> (A1((A2A3)A4)).
        """
        p = [10, 10, 10, 10, 10]
        cost, structure = matrix_chain_order(p)
        
        self.assertEqual(cost, 2000)
        self.assertEqual(structure, "(A1((A2A3)A4))")

    def test_five_identical_matrices(self):
        """
        5 square matrices [10, 10, 10, 10, 10, 10].
        Tests multi-level tie breaking across longer equal-dimension chains.
        """
        p = [10, 10, 10, 10, 10, 10]
        cost, structure = matrix_chain_order(p)
        
        self.assertEqual(cost, 3000)
        self.assertEqual(structure, "(A1((A2(A3A4))A5))")

    def test_single_and_two_matrices(self):
        """Edge cases: 1 matrix and 2 matrices."""
        self.assertEqual(matrix_chain_order([10, 20]), (0, "A1"))
        self.assertEqual(matrix_chain_order([10, 20, 30]), (6000, "(A1A2)"))

    def test_operation_summary_flag(self):
        """Ensures operation summary feature returns expected metrics without breaking legacy contract."""
        p = [10, 10, 10, 10]
        res = matrix_chain_order(p, include_summary=True)
        
        self.assertEqual(res["cost"], 1000)
        self.assertEqual(res["parenthesization"], "(A1(A2A3))")
        self.assertEqual(res["operation_summary"]["matrices_count"], 3)
        self.assertEqual(res["operation_summary"]["split_evaluations"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)