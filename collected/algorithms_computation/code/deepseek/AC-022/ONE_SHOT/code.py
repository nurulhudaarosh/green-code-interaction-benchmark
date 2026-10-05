def damerau_levenshtein(a: str, b: str) -> int:
    """
    Compute the Damerau-Levenshtein (optimal string alignment) distance
    between strings a and b. All operations cost 1:
    insertion, deletion, substitution, adjacent transposition.
    """
    m, n = len(a), len(b)

    # Trivial cases
    if m == 0:
        return n
    if n == 0:
        return m

    # Use two previous rows to keep memory O(n)
    prev2 = None                 # row i-2
    prev = list(range(n + 1))    # row i-1  (i=0)

    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(
                prev[j] + 1,              # deletion
                curr[j - 1] + 1,          # insertion
                prev[j - 1] + cost,       # match / substitution
            )
            # adjacent transposition
            if (i > 1 and j > 1
                    and a[i - 1] == b[j - 2]
                    and a[i - 2] == b[j - 1]):
                curr[j] = min(curr[j], prev2[j - 2] + 1)
        prev2, prev = prev, curr

    return prev[n]


if __name__ == "__main__":
    # Deterministic self-tests (no I/O interaction, no randomness)
    cases = [
        ("", "", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("abc", "abc", 0),
        ("abc", "abd", 1),           # substitution
        ("abc", "ab", 1),            # deletion
        ("abc", "abcd", 1),          # insertion
        ("ab", "ba", 1),             # transposition
        ("abcd", "abdc", 1),         # transposition in middle
        ("ca", "abc", 3),            # classic DL example
        ("kitten", "sitting", 3),    # classic Levenshtein example
        ("teh", "the", 1),           # transposition
        ("a cat", "an act", 3),
        ("intention", "execution", 5),
    ]

    for s1, s2, expected in cases:
        got = damerau_levenshtein(s1, s2)
        status = "OK " if got == expected else "FAIL"
        print(f"[{status}] d({s1!r}, {s2!r}) = {got} (expected {expected})")