from typing import Tuple, Dict, Any, Union


def lcs_with_reconstruction(
    s1: str, s2: str, include_summary: bool = False
) -> Union[Tuple[int, str], Tuple[int, str, Dict[str, int]]]:
    """
    Computes LCS length and deterministic LCS string reconstruction.
    
    Tie-breaking rule: Prefers advancing in s1 (i -> i - 1) whenever 
    dp[i - 1][j] == dp[i][j].
    """
    m, n = len(s1), len(s2)
    
    # 1. Build DP Table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    dp_cell_updates = 0
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp_cell_updates += 1
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
                
    lcs_length = dp[m][n]
    
    # 2. Reconstruct LCS with deterministic tie-handling
    i, j = m, n
    lcs_chars = []
    
    reconstruction_steps = 0
    s1_advancements = 0
    s2_advancements = 0
    character_matches = 0
    
    while i > 0 and j > 0:
        reconstruction_steps += 1
        
        # Rule check: Prioritize advancing in s1 if it preserves the target DP score
        if dp[i - 1][j] == dp[i][j]:
            s1_advancements += 1
            i -= 1
        elif s1[i - 1] == s2[j - 1] and dp[i - 1][j - 1] + 1 == dp[i][j]:
            character_matches += 1
            lcs_chars.append(s1[i - 1])
            i -= 1
            j -= 1
        else:
            s2_advancements += 1
            j -= 1
            
    lcs_string = "".join(reversed(lcs_chars))
    
    # Optional summary dictionary payload
    if include_summary:
        operation_summary = {
            "dp_table_cell_updates": dp_cell_updates,
            "reconstruction_steps": reconstruction_steps,
            "s1_advancements": s1_advancements,
            "s2_advancements": s2_advancements,
            "character_matches": character_matches,
        }
        return lcs_length, lcs_string, operation_summary
        
    return lcs_length, lcs_string


# Demonstrating default vs. featured usage
if __name__ == "__main__":
    s1, s2 = "ABA", "A"
    
    # Standard output (backward compatible)
    res_default = lcs_with_reconstruction(s1, s2)
    print("Standard Result:", res_default)
    
    # With operational summary enabled
    length, lcs, summary = lcs_with_reconstruction(s1, s2, include_summary=True)
    print("Length:", length)
    print("LCS String:", f"'{lcs}'")
    print("Operational Summary:", summary)