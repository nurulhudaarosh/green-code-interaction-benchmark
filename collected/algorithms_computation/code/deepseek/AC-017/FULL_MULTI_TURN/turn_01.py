import math
from typing import List, Tuple, Optional

def sieve_primes(limit: int) -> List[int]:
    """
    Generate all primes up to limit using the Sieve of Eratosthenes.
    """
    if limit < 2:
        return []
    
    is_prime = [True] * (limit + 1)
    is_prime[0] = is_prime[1] = False
    
    for i in range(2, int(math.sqrt(limit)) + 1):
        if is_prime[i]:
            for j in range(i * i, limit + 1, i):
                is_prime[j] = False
    
    return [i for i in range(2, limit + 1) if is_prime[i]]

def segmented_sieve(L: int, R: int) -> Tuple[List[int], Optional[int]]:
    """
    Find all primes in [L, R] using segmented sieve.
    Returns tuple: (list of primes, largest gap between consecutive primes)
    Returns None for gap if there are fewer than 2 primes.
    """
    if L > R:
        return [], None
    
    # Handle edge cases
    L = max(L, 2)  # No primes less than 2
    if L > R:
        return [], None
    
    # Generate base primes up to sqrt(R)
    limit = int(math.sqrt(R)) + 1
    base_primes = sieve_primes(limit)
    
    # Segmented sieve for [L, R]
    segment_size = R - L + 1
    is_prime = [True] * segment_size
    
    for p in base_primes:
        # Find the first multiple of p in [L, R]
        # Starting point: max(p*p, ceil(L/p) * p)
        start = max(p * p, ((L + p - 1) // p) * p)
        
        for multiple in range(start, R + 1, p):
            is_prime[multiple - L] = False
    
    # Collect primes in the segment
    primes = []
    for i in range(segment_size):
        if is_prime[i]:
            primes.append(L + i)
    
    # Calculate largest gap
    largest_gap = None
    if len(primes) >= 2:
        largest_gap = max(primes[i+1] - primes[i] for i in range(len(primes) - 1))
    
    return primes, largest_gap

def solve(L: int, R: int) -> None:
    """
    Main solver function that prints the result for interval [L, R].
    """
    primes, largest_gap = segmented_sieve(L, R)
    
    if not primes:
        print(f"No primes in [{L}, {R}]")
    elif largest_gap is None:
        print(f"Only one prime in [{L}, {R}]: {primes[0]}")
    else:
        print(f"Primes in [{L}, {R}]: {primes}")
        print(f"Largest gap between consecutive primes: {largest_gap}")

# Example usage
if __name__ == "__main__":
    # Test cases
    test_cases = [
        (10, 30),
        (1, 10),
        (14, 16),
        (2, 3),
        (100, 200),
        (1000000, 1000100)
    ]
    
    for L, R in test_cases:
        print(f"\n--- Interval [{L}, {R}] ---")
        solve(L, R)